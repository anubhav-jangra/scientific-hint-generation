import os
os.environ["HF_HOME"] = "" # replace with your huggingface cache directory
MY_HF_TOKEN = "" # replace with your huggingface token

import tqdm
import json
import random
random.seed(42)

import argparse

import torch
from transformers import AutoModelForSeq2SeqLM, AutoModelForCausalLM, AutoTokenizer

from autoeval_utils import fetch_answer

eval_data_path = "../../data/HintGenDataset/valid.json"
out_dir = "output"
MAX_CHAIN_SIZE = 30
MODEL_NAMES = ['google/gemma-2-2b', 'google/gemma-2-9b',
               'meta-llama/Llama-3.2-1B-Instruct', 'meta-llama/Llama-3.2-3B-Instruct', 'meta-llama/Llama-3.1-8B-Instruct',
               'Qwen/Qwen3-0.6B', 'Qwen/Qwen3-1.7B', 'Qwen/Qwen3-4B', 'Qwen/Qwen3-8B',
               'Qwen/Qwen2.5-0.5B-Instruct', 'Qwen/Qwen2.5-1.5B-Instruct', 'Qwen/Qwen2.5-3B-Instruct', 'Qwen/Qwen2.5-7B-Instruct',
               'Qwen/Qwen2.5-0.5B', 'Qwen/Qwen2.5-1.5B', 'Qwen/Qwen2.5-3B', 'Qwen/Qwen2.5-7B',
               'mistralai/Mistral-7B-Instruct-v0.2']

def get_chain_prompt(question, hints, hint_idx, eval_type="combined"):
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

if __name__ == "__main__":

    # initialize the argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', "--model")
    parser.add_argument('-b', "--batch_size")
    parser.add_argument("--precision", action='store_true', help="If true, use fp16 precision")
    args = parser.parse_args()
    model_name = args.model
    BATCH_SIZE = int(args.batch_size)
    print(f"Running evaluation for model: {model_name} with batch size: {BATCH_SIZE} with precision switch set as: {args.precision}")

    # create the outdir
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # check if the output file already exists
    if os.path.exists(os.path.join(out_dir, f"{model_name.split('/')[-1]}_maxchain-{MAX_CHAIN_SIZE}.json")):
        print(f"Output file already exists for model: {model_name}. Skipping evaluation.")
        import sys; sys.exit(0)

    # load the dataset
    eval_data = json.load(open(eval_data_path))
    
    # ===== PREPROCESS =====

    # preprocess the dataset to the desired prompting format. 
    prompts = []
    for inst in eval_data:
        question = inst["question"]
        # randomly obtain MAX_CHAIN_SIZE hints
        hints = [hint.split('\t')[-1] for hint in inst["hints"].split('\n')]
        random.shuffle(hints)
        hint_chain = hints[:MAX_CHAIN_SIZE]

        # add the base hint-less prompt
        prompts.append(f"Answer the following question succinctly: \nQuestion: {question}\nAnswer: ")

        # create prompts for each hint in the chain
        for hint_idx in range(len(hint_chain)):
            prompt = get_chain_prompt(question, hint_chain, hint_idx, eval_type="combined")
            prompts.append(prompt)
    
    # ===== INFERENCE =====
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # model, generate the completions
    if args.precision:
        model = AutoModelForCausalLM.from_pretrained(model_name, token=MY_HF_TOKEN).to(device).to(torch.bfloat16)
    else:
        model = AutoModelForCausalLM.from_pretrained(model_name, token=MY_HF_TOKEN).to(device)
    tokenizer = AutoTokenizer.from_pretrained(model_name, token=MY_HF_TOKEN)
    if 'Qwen' in model_name:
        tokenizer.padding_side = 'left'
    # Set pad_token to eos_token if pad_token is not set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    # Explicitly set pad_token_id to eos_token_id
    model.config.pad_token_id = model.config.eos_token_id

    # generate the completions
    completions = []
    for i in tqdm.trange(0, len(prompts), BATCH_SIZE):
        batch = prompts[i:i+BATCH_SIZE]
        # if args.precision:
        #     inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True).to(device).to(torch.bfloat16)
        # else:
        #     inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True).to(device)
        # # Cast only the attention mask to bfloat16
        # inputs = {k: (v.to(torch.bfloat16) if k != 'input_ids' else v) for k, v in inputs.items()}
        inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True).to(device)
        outputs = model.generate(**inputs, max_new_tokens=50)  # Set max_new_tokens to control the number of tokens generated
        completions.extend(tokenizer.batch_decode(outputs, skip_special_tokens=True))

    # ===== EVALUATION =====
    # parse the completions
    answers = [fetch_answer(completion) for completion in completions]

    # collect the instance level answers for each prompt
    # take every 0 to MAX_CHAIN_SIZE+1-th chunk (+1 for the base instance) of answer and store it in instance_level_answers
    instance_level_answers = [answers[i:i+MAX_CHAIN_SIZE+1] for i in range(0, len(answers), MAX_CHAIN_SIZE+1)]

    # return the instance level answers
    json.dump(instance_level_answers, open(os.path.join(out_dir, f"{model_name.split('/')[-1]}_maxchain-{MAX_CHAIN_SIZE}.json"), 'w'))
