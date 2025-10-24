# from utils import get_label_rouge #, get_label_nli, get_label_bertscore
from rouge_score import rouge_scorer

def fetch_answer(generation_string):
    """
    A function that fetches the answer from the generation string. It takes care of different formats of the generation string.
    """
    string = generation_string.lower()
    # check if there are multiple questions (over generations from LLMs)
    if string.count("question:") >= 1:
        # if there are, then only keep the first question
        string = string.split("question:")[1].strip()
    
    # check if the answer is present in the string
    if "answer:" in string:
        # if the answer is present, then extract the answer
        string = string.split("answer:")[1]
    
    # for some specific model resposnes - 
    if "<|file_separator|>" in string:
        string = string.split("<|file_separator|>")[0]
    
    # for some specific model resposnes -
    if "assisstant" in string:
        string = string.split("assisstant")[1]
    
    # strip off any white spaces
    string = string.strip()
    return string

def get_label_rouge(answer, prediction):
    """
    A function that returns rouge score between the answer and prediction.

    Args:
        answer (str): The correct answer.
        prediction (str): The predicted answer.
    
    Returns:
        # dict: rouge scores (r1, r2, rl) between the answer and prediction.
        tuple: rouge scores (r1, r2, rl) between the answer and prediction.
    """
    
    # lowercase the answer and prediction
    answer = answer.lower()
    prediction = prediction.lower()

    # obtain the answer from the prediction string
    prediction = fetch_answer(prediction)

    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(answer, prediction)
    rouge1, rouge2, rougeL = scores['rouge1'].recall, scores['rouge2'].recall, scores['rougeL'].recall
    return (rouge1, rouge2, rougeL)