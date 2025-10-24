import os
import json

import sys
sys.path.append('../autoeval')
from autoeval import AutoEvalHints

out_dir = "output/baseline_generations"

# initialize the hint evaluator
align_score_checkpoint_path = "autoeval/AlignScore/models/AlignScore-large.ckpt"
hint_evaluator = AutoEvalHints(log_dir='output/eval_logs', alignscore_checkpoint_path=align_score_checkpoint_path)

if __name__ == "__main__":
    # load the validation dataset for evaluation of hint generation systems
    valid_data_path = "../data/SciQ-HintGen/valid.json" # path to the validation data with pregenerated 80 hints for reference-free consistency evaluation
    eval_data = json.load(open(valid_data_path, 'r'))
    # convert eval_data into a dict with question as keys (needed to match the evaluation script needs)
    eval_data_dict = {inst['question']: {'all_hints': [hint.split('\t')[-1].strip() for hint in inst['hints'].split('\n')],
                                        'domain': inst['domain'],
                                        'context': inst['context'],
                                        'answer': inst['answer']} for inst in eval_data}
    
    model_names = ["mistral-small:24b",
                   "gemma3:1b", "gemma3:4b", "gemma3:12b", "gemma3:27b",
                   "deepseek-r1:1.5b", "deepseek-r1:7b", "deepseek-r1:8b", "deepseek-r1:14b", "deepseek-r1:32b",
                   "qwen3:0.6b", "qwen3:1.7b", "qwen3:4b", "qwen3:8b", "qwen3:14b", "qwen3:30b",
                   "phi4:14b"]

    for model_name in model_names:
        print(f"Evaluating hints for model: {model_name}")
        # check if results file already exists and skip
        if os.path.exists(os.path.join(out_dir, f"{model_name.replace(':', '-')}_static_valid_results.json")) and \
           os.path.exists(os.path.join(out_dir, f"{model_name.replace(':', '-')}_dynamic_valid_results.json")):
            print(f"Results already exist for model {model_name}, skipping...")
            continue
        # check that the base and adaptive generated hints are in the output directory
        if not os.path.exists(os.path.join(out_dir, f"{model_name.replace(':', '-')}_static_valid.json")):
            raise ValueError(f"Output file {model_name.replace(':', '-')}_static_valid.json does not exist in {out_dir}. Please run the generation script first.")
        if not os.path.exists(os.path.join(out_dir, f"{model_name.replace(':', '-')}_dynamic_valid.json")):
            raise ValueError(f"Output file {model_name.replace(':', '-')}_dynamic_valid.json does not exist in {out_dir}. Please run the generation script first.")

        base_hints = json.load(open(os.path.join(out_dir, f"{model_name.replace(':', '-')}_static_valid.json"), 'r'))
        adaptive_hints = json.load(open(os.path.join(out_dir, f"{model_name.replace(':', '-')}_dynamic_valid.json"), 'r'))

        # combine the validation data with the base and adaptive hints
        base_hints_final = []
        adaptive_hints_final = []
        for question, data in eval_data_dict.items():
            base_hint = base_hints.get(question, [])
            adaptive_hint = adaptive_hints.get(question, [])
            assert len(base_hint) == 4, f"Expected 4 hints for question {question}, got {len(base_hint)}"
            assert len(adaptive_hint) == 4, f"Expected 4 adaptive hints for question {question}, got {len(adaptive_hint)}"
            
            if not base_hint or not adaptive_hint:
                continue
            
            base_hints_final.append({
                'question': question,
                'domain': data['domain'],
                'context': data['context'],
                'answer': data['answer'],
                'all_hints': data['all_hints'],
                'hint_chain': base_hint
            })
            
            adaptive_hints_final.append({
                'question': question,
                'domain': data['domain'],
                'context': data['context'],
                'answer': data['answer'],
                'all_hints': data['all_hints'],
                'hint_chain': adaptive_hint
            })

        if not os.path.exists(os.path.join(out_dir, f"{model_name.replace(':', '-')}_static_valid_results.json")):
            print("Evaluating static hints...")
            results = hint_evaluator.evaluate_corpus(base_hints_final, experiment_name=f"{model_name.replace(':', '-')}_static_valid")
            # Save the results to a JSON file
            json.dump(results, open(os.path.join(out_dir, f"{model_name.replace(':', '-')}_static_valid_results.json"), 'w'), indent=4)
        else:
            print(f"Static hints results already exist for {model_name}. Skipping evaluation.")

        if not os.path.exists(os.path.join(out_dir, f"{model_name.replace(':', '-')}_dynamic_valid_results.json")):
            print("Evaluating dynamic hints...")
            adaptive_results = hint_evaluator.evaluate_corpus(adaptive_hints_final, experiment_name=f"{model_name.replace(':', '-')}_dynamic_valid")
            # Save the results to a JSON file
            json.dump(adaptive_results, open(os.path.join(out_dir, f"{model_name.replace(':', '-')}_dynamic_valid_results.json"), 'w'), indent=4)
        else:
            print(f"Dynamic hints results already exist for {model_name}. Skipping evaluation.")