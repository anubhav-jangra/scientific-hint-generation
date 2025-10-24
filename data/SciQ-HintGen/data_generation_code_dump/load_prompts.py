import json

def get_prompts(prompts_path):
    """
        A function to fetch the prompts from a .json file.
    """
    with open(prompts_path, 'r') as prompt_file:
        prompts = json.load(prompt_file)

    return prompts
