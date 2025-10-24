import os
import json
MY_HF_TOKEN = None # replace with your HF token if needed

import tqdm
import requests
import numpy as np

import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords 
from sklearn.feature_extraction.text import CountVectorizer
from nltk.tokenize import word_tokenize
from nltk.util import ngrams
from scipy.stats import entropy

import torch
import torch.nn.functional as F

import torch._dynamo
torch._dynamo.config.suppress_errors = True
os.environ['TORCHDYNAMO_DISABLE'] = '1'

from sentence_transformers import SentenceTransformer
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

import sys
sys.path.append('AlignScore/src')
from alignscore import AlignScore # local clone of the repo - https://github.com/yuh-zha/AlignScore

sys.path.append('py_readability_metrics')
from py_readability_metrics.readability.readability import Readability

from autoeval_utils import fetch_answer, get_label_rouge

class AutoEvalHints():

    def __init__(self, log_dir=None, info_gain_model_name='google/gemma-2-9b', alignscore_checkpoint_path="AlignScore/models/AlignScore-large.ckpt"):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        if log_dir is not None:
            os.makedirs(log_dir, exist_ok=True)
            os.makedirs(os.path.join(log_dir, 'leakage_logs'), exist_ok=True)
        self.log_dir = log_dir

        # answerability model init (only works for text-generation causal LLMs with current implementation)
        # Determine the appropriate model class and pipeline task
        self.info_gain_model = AutoModelForCausalLM.from_pretrained(info_gain_model_name, token=MY_HF_TOKEN).to(self.device).to(torch.bfloat16)
        self.info_gain_tokenizer = AutoTokenizer.from_pretrained(info_gain_model_name, token=MY_HF_TOKEN)
        self.info_batch_size = 16

        # Create the pipeline
        print(f"===== Loaded the information gain model {info_gain_model_name} =====")

        # self-redundancy model init
        self.stsb_model = SentenceTransformer('sentence-transformers/bert-large-nli-stsb-mean-tokens', device=self.device, cache_folder=os.environ['HF_HOME'])
        print("===== Loaded the sentence bert model for self-referenced redundancy model =====")

        # consistency morel init
        self.consistency_batch_size = 32
        self.consistency_scorer = AlignScore(model='roberta-base', batch_size=self.consistency_batch_size, device=self.device, ckpt_path=alignscore_checkpoint_path, evaluation_mode='nli_sp')
        print("===== Loaded the consistency scorer model from align-score (underlying model roberta-large) =====")

    def evaluate_corpus(self, instances, experiment_name=None, return_instance_level=False):
        # corpus is a list of dictionaries, 
        # each dictionary contains question, answer, context, all_hints, hint_chain for a single instance
        results = {}
        results['info_gain'] = self.eval_info_gain(instances, experiment_name, return_instance_level=return_instance_level)
        results['redundancy'] = self.eval_redundancy(instances, return_instance_level=return_instance_level)
        results['consistency'] = self.eval_consistency(instances, return_instance_level=return_instance_level)
        results['readability'] = self.eval_readability(instances, return_instance_level=return_instance_level)
        results['leakage'] = self.evaluate_leakage(instances, experiment_name, return_instance_level=return_instance_level)

        return results

    def eval_info_gain(self, instances, experiment_name=None, return_instance_level=False):
        
        def get_chain_prompt(question, hints, hint_idx, eval_type="individual"):
            """
            Generate the prompt for the chain of hints evaluation
            
            Args:
                question (str)  : the question
                hints (list)    : list of hints (chain of hints)
                hint_idx (int)  : index of the hint to be included in the prompt
                eval_type (str) : type of evaluation (individual or combined). Individual returns a single hint, combined returns all hints till the hint_idx.
            """

            assert hint_idx < len(hints), "Hint index out of bounds"
            prompt = f"Answer the following question succinctly: \nQuestion: {question}\n"
            if eval_type == "individual":
                prompt += f"Hint: {hints[hint_idx]}\n"
            else:
                for i, hint in enumerate(hints[:hint_idx+1]):
                    prompt += f"Hint {i+1}: {hint}\n"
            prompt += "Answer: "

            return prompt
        
        # get the hint_chain size
        chain_size = len(instances[0]['hint_chain'])

        # check if the experiment results already exist, if they do, load them up
        experiment_file = os.path.join(self.log_dir, f"{experiment_name}.json")

        if experiment_name is not None and self.log_dir is not None and os.path.exists(experiment_file):
            instance_level_predictions = json.load(open(experiment_file, 'r'))
            print("Loaded the instance level predictions from the existing experiment file...")
        else:
            # develop the prompts for model inference
            prompts = []
            for inst in instances:
                # first obtain the flat qa response for the question without any hints
                qa_prompt = f"Answer the following question succinctly: \nQuestion: {inst['question']}\nAnswer: "
                prompts.append(qa_prompt)
                # for each hint in the hint chain, obtain the individual prompt
                for hint_idx in range(len(inst['hint_chain'])):
                    prompts.append(get_chain_prompt(inst['question'], inst['hint_chain'], hint_idx, eval_type="individual"))
                # for each hint in the hint chain, obtain the combined prompt
                for hint_idx in range(len(inst['hint_chain'])):
                    prompts.append(get_chain_prompt(inst['question'], inst['hint_chain'], hint_idx, eval_type="combined"))
                    
            # obtain the responses from the model
            print("Executing the information gain model")
            completions = []
            for i in tqdm.trange(0, len(prompts), self.info_batch_size):
                batch = prompts[i:i+self.info_batch_size]
                inputs = self.info_gain_tokenizer(batch, return_tensors="pt", padding=True, truncation=True).to(self.device)
                # Cast only the attention mask to bfloat16
                inputs = {k: (v.to(torch.bfloat16) if k != 'input_ids' else v) for k, v in inputs.items()}
                try:
                    outputs = self.info_gain_model.generate(**inputs, max_new_tokens=50)  # Set max_new_tokens to control the number of tokens generated
                except Exception as e:
                    print(f"Error in generating outputs for batch starting at index {i}: {e}")
                    print("Retrying with smaller batch size of 1...")
                    # Retry with batch size of 1
                    for j in range(len(batch)):
                        single_input = self.info_gain_tokenizer(batch[j], return_tensors="pt", padding=True, truncation=True).to(self.device)
                        single_input = {k: (v.to(torch.bfloat16) if k != 'input_ids' else v) for k, v in single_input.items()}
                        try:
                            single_output = self.info_gain_model.generate(**single_input, max_new_tokens=50)
                            single_completion = self.info_gain_tokenizer.batch_decode(single_output, skip_special_tokens=True)
                            completions.extend(single_completion)
                        except Exception as e2:
                            print(f"Error in generating output for single input at index {i+j}: {e2}. Prompt: {batch[j]}")
                            raise ValueError("Generation failed even with batch size of 1. Please check the model and input.")
                completions.extend(self.info_gain_tokenizer.batch_decode(outputs, skip_special_tokens=True))

            # parse the completions
            answers = [fetch_answer(completion) for completion in completions]

            # a more generic gathering mechanism that does not assume same hint chain size
            instance_level_predictions = []
            # collect the instance level answers for each prompt
            counter = 0
            for inst in instances:
                chain_size = len(inst['hint_chain'])
                num_answers = 2*chain_size + 1
                inst = {'qa': answers[counter],
                        'individual_answers': answers[counter+1:counter+chain_size+1],
                        'combined_answers': answers[counter+chain_size+1:counter+2*chain_size+1]}
                instance_level_predictions.append(inst)
                counter += num_answers

            # save the completions
            if experiment_name is not None and self.log_dir is not None:
                with open(experiment_file, 'w') as f:
                    json.dump(instance_level_predictions, f, indent=2)
        
        if not return_instance_level:
            # evaluate the rouge gains for individual and combined hint inferences
            rouge_gains = {'individual': {'r1': 0, 'r2': 0, 'rL': 0}, # mean rouge gains for individual hints
                        'combined': {'r1': 0, 'r2': 0, 'rL': 0} # max rouge gains for combined hints
                        }
            for inst, predictions in zip(instances, instance_level_predictions):
                # evaluate the qa response
                qa_response = predictions['qa']
                answer = inst['answer']
                qa_scores = get_label_rouge(answer, qa_response)
                # evaluate the generated answers 
                # obtain the mean rouge gains for individual hints strategy
                for rouge_idx, rouge_type in enumerate(['r1', 'r2', 'rL']):
                    rouge_gains['individual'][rouge_type] += np.mean([get_label_rouge(answer, response)[rouge_idx] - qa_scores[rouge_idx] for response in predictions['individual_answers']])
                # obtain the max rouge gains for combined hints strategy
                for rouge_idx, rouge_type in enumerate(['r1', 'r2', 'rL']):
                    rouge_gains['combined'][rouge_type] += np.max([get_label_rouge(answer, response)[rouge_idx] - qa_scores[rouge_idx] for response in predictions['combined_answers']])

            # average the rouge gains over all instances
            for eval_type in ['individual', 'combined']:
                for metric in ['r1', 'r2', 'rL']:
                    rouge_gains[eval_type][metric] /= len(instances)
        else:
            rouge_gains = {'individual': {'r1': [], 'r2': [], 'rL': []}, # mean rouge gains for individual hints
                           'combined': {'r1': [], 'r2': [], 'rL': []}, # max rouge gains for combined hints
                           'individual_hint': {'r1': [], 'r2': [], 'rL': []} # list of lists
                        }
            for inst, predictions in zip(instances, instance_level_predictions):
                # evaluate the qa response
                qa_response = predictions['qa']
                answer = inst['answer']
                qa_scores = get_label_rouge(answer, qa_response)
                # evaluate the generated answers 
                # obtain the mean rouge gains for individual hints strategy
                for rouge_idx, rouge_type in enumerate(['r1', 'r2', 'rL']):
                    rouge_gains['individual_hint'][rouge_type].append([get_label_rouge(answer, response)[rouge_idx] - qa_scores[rouge_idx] for response in predictions['individual_answers']])
                for rouge_idx, rouge_type in enumerate(['r1', 'r2', 'rL']):
                    rouge_gains['individual'][rouge_type].append(np.mean([get_label_rouge(answer, response)[rouge_idx] - qa_scores[rouge_idx] for response in predictions['individual_answers']]))
                # obtain the max rouge gains for combined hints strategy
                for rouge_idx, rouge_type in enumerate(['r1', 'r2', 'rL']):
                    rouge_gains['combined'][rouge_type].append(np.max([get_label_rouge(answer, response)[rouge_idx] - qa_scores[rouge_idx] for response in predictions['combined_answers']]))
        
        return rouge_gains


    def eval_redundancy(self, instances, return_instance_level=False):
        # get unique n-gram metric and normalized inverse of diversity from -
        # paper - https://aclanthology.org/2020.aacl-main.51.pdf
        # github - https://github.com/Wendy-Xiao/redundancy_reduction_longdoc/blob/master/utils.py

        # sourced from - https://github.com/Wendy-Xiao/redundancy_reduction_longdoc/blob/master/utils.py
        def get_redundancy_scores(text):
            stop_words = set(stopwords.words('english'))
            count = CountVectorizer()

            all_txt = word_tokenize(text)

            # uniq n-gram ratio
            all_unigram = list(ngrams(all_txt,1))
            uniq_unigram = set(all_unigram)
            unigram_ratio = len(uniq_unigram)/len(all_unigram)

            all_bigram = list(ngrams(all_txt,2))
            uniq_bigram = set(all_bigram)
            bigram_ratio = len(uniq_bigram)/len(all_bigram)

            all_trigram = list(ngrams(all_txt,3))
            uniq_trigram = set(all_trigram)
            trigram_ratio = len(uniq_trigram)/len(all_trigram)

            # NID score
            num_word = len(all_txt)
            all_txt = [w for w in all_txt if not w in stop_words]
            all_txt = [' '.join(all_txt)]

            x = count.fit_transform(all_txt)
            bow = x.toarray()[0]
            # max_possible_entropy = entropy(np.ones(bow.shape))
            # num_word = sum(bow)
            # print(num_word)
            max_possible_entropy = np.log(num_word)
            e = entropy(bow)
            redundancy = (1-e/max_possible_entropy)
            return unigram_ratio, bigram_ratio, trigram_ratio, redundancy

        unigram_scores, bigram_scores, trigram_scores, redundancy_scores = [], [], [], []
        for inst in instances:
            try:
                unigram_ratio, bigram_ratio, trigram_ratio, redundancy = get_redundancy_scores(" ".join(inst['hint_chain']))
                unigram_scores.append(unigram_ratio)
                bigram_scores.append(bigram_ratio)
                trigram_scores.append(trigram_ratio)
                redundancy_scores.append(redundancy)
            except Exception as e:
                print(f"Error in calculating redundancy scores for instance {inst['question']}: {e}")
                unigram_scores.append(0)
                bigram_scores.append(0)
                trigram_scores.append(0)
                redundancy_scores.append(0)

        # get the self-referenced redundancy score from - 
        # paper - https://aclanthology.org/2021.acl-long.34.pdf
        # github - https://github.com/Chen-Wang-CUHK/Training-Free-and-Ref-Free-Summ-Evaluation/tree/main

        # idea from Section 3.2 of https://aclanthology.org/2021.acl-long.34.pdf
        def get_self_referenced_redundancy_scores(hints): # sentence level implementation
            # hints : list of strings
            # returns : float between -1 and 1
            embeds = self.stsb_model.encode(hints)
            redundancy_score = 0
            for idx1, sent1 in enumerate(embeds):
                max_sim = -1.0
                for idx2, sent2 in enumerate(embeds):
                    if idx1 == idx2:
                        continue
                    cos_sim = F.cosine_similarity(torch.tensor(sent1).to(self.device), torch.tensor(sent2).to(self.device), dim=0)
                    max_sim = max(max_sim, cos_sim)
                redundancy_score += max_sim
            return redundancy_score/len(hints)

        self_referenced_scores = []
        for inst in instances:
            if len(inst['hint_chain']) == 0:
                self_referenced_scores.append(0)
                continue
            self_referenced = get_self_referenced_redundancy_scores(inst['hint_chain'])
            self_referenced_scores.append(float(self_referenced))
        
        if return_instance_level:
            return {'unigram_ratio': unigram_scores, 
                    'bigram_ratio': bigram_scores, 
                    'trigram_ratio': trigram_scores, 
                    'nid': redundancy_scores,
                    'self_referenced': self_referenced_scores
                }
        else:
            return {'unigram_ratio': np.mean(unigram_scores), 
                    'bigram_ratio': np.mean(bigram_scores), 
                    'trigram_ratio': np.mean(trigram_scores), 
                    'nid': np.mean(redundancy_scores),
                    'self_referenced': np.mean(self_referenced_scores)
                }

    def eval_consistency(self, instances, return_instance_level=False): 
        # a bit tricky to evaluate hint consistency (due to incomplete information in the hints)
        # a proxy for coverage of content from the hints
        # taken from - https://arxiv.org/abs/2305.16739
        # github repo - https://github.com/yuh-zha/AlignScore

        # idea is to use context, but since it's not always present, 
        # a reference-free approach is to use the collection of hints as the source of information
        
        # for context, we'll use all the hints without the hints in the hint chain
        # for claims, we'll use the hint chain

        hint_consistency_scores, context_consistency_scores = [], []
        for i in range(0, len(instances), self.consistency_batch_size):
            batch = instances[i:i + self.consistency_batch_size]
            hint_contexts = [" ".join(set(inst['all_hints']) - set(inst['hint_chain'])) for inst in batch] # pseudo context
            actual_contexts = [inst['context'] for inst in batch] # actual context
            claims = [" ".join(inst['hint_chain']) for inst in batch]

            batch_hint_consistency_scores = self.consistency_scorer.score(contexts=hint_contexts, claims=claims)

            # Check if context is not none and calculate consistency score for context
            # find out non-empty contexts and claims
            non_empty_context_claims = [(context, claim) for context, claim in zip(actual_contexts, claims) if context is not None]
            empty_context_size = len(actual_contexts) - len(non_empty_context_claims)
            non_empty_contexts, non_empty_claims = zip(*non_empty_context_claims)

            batch_context_consistency_scores = self.consistency_scorer.score(contexts=non_empty_contexts, claims=non_empty_claims)
            batch_context_consistency_scores = list(batch_context_consistency_scores) + [0.0] * empty_context_size # fill in the empty context scores with 0 -?? (should I do this?)

            hint_consistency_scores.extend(batch_hint_consistency_scores)
            context_consistency_scores.extend(batch_context_consistency_scores)
        
        if return_instance_level:
            return {'hint_consistency': hint_consistency_scores, 'context_consistency': context_consistency_scores}
        else:
            return {'align_score_hints': np.mean(hint_consistency_scores), 'align_score_context': np.mean(context_consistency_scores)}


    def eval_readability(self, instances, return_instance_level=False):
        # Taken from - https://arxiv.org/pdf/2407.00747v1
        # use the github repo - https://github.com/cdimascio/py-readability-metrics
        
        readability_scores = {'flesch_kincaid': [], # Flesch-Kincaid Grade Level
                              'fre': [], # Flesch Reading Ease
                              'dale_chall': [], # Dale-Chall Readability Score
                                }
        for inst in instances:
            r = Readability(' '.join(inst['hint_chain']))
            try:
                readability_scores['flesch_kincaid'].append(r.flesch_kincaid().score)
            except Exception as e:
                print(f"Error in calculating Flesch-Kincaid score for instance {inst['question']}: {e}")
                readability_scores['flesch_kincaid'].append(0)
            try:
                readability_scores['fre'].append(r.flesch().score)
            except Exception as e:
                print(f"Error in calculating Flesch Reading Ease score for instance {inst['question']}: {e}")
                readability_scores['fre'].append(0)
            try:
                readability_scores['dale_chall'].append(r.dale_chall().score)
            except Exception as e:
                print(f"Error in calculating Dale-Chall score for instance {inst['question']}: {e}")
                readability_scores['dale_chall'].append(0)
        
        # normalize the scores
        for key in readability_scores:
            readability_scores[key] = np.mean(readability_scores[key]) if not return_instance_level else readability_scores[key]
        return readability_scores
    

    def evaluate_leakage_em(self, instances, return_instance_level=False):
        leaked_hints = []
        for inst in instances:
            answer = inst['answer']
            hints = inst['hint_chain']
            leakage_arr = []
            # check if the answer is leaked in the hints
            for hint in hints:
                if answer.lower() in hint.lower():
                    leakage_arr.append(1)
                else:
                    leakage_arr.append(0)
            leaked_hints.append(leakage_arr)

        if return_instance_level:
            return leaked_hints
        else:
            # return the percentage of leaked hints
            total_hints = sum([len(arr) for arr in leaked_hints])
            total_leaked_hints = sum([sum(arr) for arr in leaked_hints])
            return total_leaked_hints / total_hints

    def evaluate_leakage_llm(self, instances, experiment_name, return_instance_level=False):
        leakage_prompt = """You are a helpful assistant that helps evaluate the hints generated by a model. You are given a question and a set of hints. Your task is determine if the hints reveal too much information about the answer to the question. If the hints reveal too much information, then return "Yes", otherwise return "No". Only return "Yes" or "No" as the answer.

Question: {question}
Answer: {answer}
Hints: {hints}
"""
        OLLAMA_URL = "http://localhost:11434/api/generate" # replace with your OLLAMA server URL
        evaluation_model_name = "gemma3:27b"

        # check if the leakage results file already exists
        if os.path.exists(os.path.join(self.log_dir, 'leakage_logs', f"{experiment_name}.json")):
            print(f"Leakage results for {experiment_name} already exist. Skipping...")
            leakage_responses = json.load(open(os.path.join(self.log_dir, 'leakage_logs', f"{experiment_name}.json"), 'r'))
        else:
            leakage_responses = {}
            for inst in instances:
                # prepare the payload
                payload = {
                    "model": evaluation_model_name,
                    "prompt": leakage_prompt.format(question=inst['question'], answer=inst['answer'], hints="\n".join(inst['hint_chain'])),
                    "stream": False,
                    "options": {"temperature": 0.0} # deterministic output
                }

                # send the request to the OLLAMA server
                response = requests.post(OLLAMA_URL, json=payload)
                if response.status_code == 200:
                    leakage = response.json()
                    leakage_responses[inst['question']] = leakage['response'].strip()
                else:
                    print(f"Error: {response.status_code} - {response.text} for question: {inst['question']}")
            
            # save the leakage responses
            if self.log_dir is not None:
                json.dump(leakage_responses, open(os.path.join(self.log_dir, 'leakage_logs', f"{experiment_name}.json"), 'w'), indent=4)
        
        if return_instance_level:
            return list(leakage_responses.values())
        else:
            # return the percentage of leaked hints
            leakage_percent = sum([1 for v in leakage_responses.values() if "yes" in v.lower()]) / len(leakage_responses) * 100
            return leakage_percent

    def evaluate_leakage(self, instances, experiment_name, return_instance_level=False):
        # leakage can be evaluated in two ways - exact match or LLM based
        # exact match is a bit too strict, so we'll use LLM based approach
        # for now, we'll implement exact match based approach
        return {'em': self.evaluate_leakage_em(instances, return_instance_level=return_instance_level),
                'llm': self.evaluate_leakage_llm(instances, experiment_name, return_instance_level=return_instance_level)}