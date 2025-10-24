import os
import json
import requests

def get_offline_hint(question, past_hints, hintgen_data_dir):
    """ A function to get offline hints for a given question.
    Args:
        question: the question for which hints are to be generated
        past_hints: list of past hints shown to the user
    Returns:
        hint: a hint for the given question. The hint is a string that provides additional information to help answer the question.
    If no hints are available or all hints have been shown, returns None.
    """
    # load the pre-defined hints and return the next hint
    offline_hints = json.load(open(os.path.join(hintgen_data_dir, 'quiz_with_offline_hints.json'), 'r'))
    hints = offline_hints.get(question, [])
    if not hints:
        return None
    for hint in hints:
        if hint not in past_hints:
            return hint
    return None

def clean_hint(hint, hint_chain_size):
    # Remove any leading/trailing whitespace
    hint = hint.strip()

    # remove the thinking part if it exists
    if '</think>' in hint:
        hint = hint.split('</think>')[-1].strip()
    
    # Remove any unwanted characters or formatting
    hint = hint.replace('\n', ' ').replace('\r', '')
    
    # Remove the unwanted starters from the hint
    unwanted_starters = ['- ', ' -', '•', ' •', ':']
    for i in range(1, hint_chain_size+1):
        unwanted_starters.append(f'Hint {i} - ')
        unwanted_starters.append(f'- **Hint {i}**')
        unwanted_starters.append(f'**Hint {i}**')
        unwanted_starters.append(f'**Hint {i}:**')
        unwanted_starters.append(f'Hint {i}')
    
    unwanted_starters.append(':')
    unwanted_starters.append('-')
    
    for starter in unwanted_starters:
        if hint.startswith(starter):
            hint = hint[len(starter):].strip()

    # Remove any extra spaces
    hint = ' '.join(hint.split())

    return hint

def get_online_hint(question, correct_answer, conversation_str, past_attempts, past_hints):
    """A function to get online hints for a given question. It calls the locally hosted model using a ngrok tunnel.
    Args:
        question: the question for which hints are to be generated
        conversation_str: the conversation string containing the past responses and hints shown to the user (comprising of past hints shown, and the user's attempts).
        past_attempts: list of past attempts made by the user
        past_hints: list of past hints shown to the user
    Returns:
        hint: a hint for the given question. The hint is a string that provides additional information to help answer the question.
    If no hints are available or all hints have been shown, returns None.
    Note: This function is a placeholder and should be implemented to call the actual model API
    """
    OLLAMA_URL = "" # Replace with your generation URL
    # get the correct answer corresponding to the question
    prompt = f"""Generate a single hint for this question-answer pair that will help a learner answer the question. The hint should be concise and clear, guiding the learner towards the correct answer without revealing it. The hint should be a single sentence or phrase. You are provided with the interaction of the learner with the system so far, including their attempted answers and previous hints. Use the information from their interaction to provide a useful hint to help them answer the question. Generate the hint directly in a bullet point format.

Question: {{question}}
Answer: {{answer}}
{{conversation_str}}
Hint:
""".format(question=question, answer=correct_answer, conversation_str=conversation_str)
    
    payload = {
                "model": "mistral-small:24b",
                "prompt": prompt,
                "stream": False
            }
    response = requests.post(OLLAMA_URL, json=payload)
    if response.status_code == 200:
        hint = response.json()['response'].strip()
        hint = clean_hint(hint, 4)
    else:
        hint = f"Error: {response.status_code} - {response.text}"
    return hint