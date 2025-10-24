# A file containing the data-related utility functions (used in main_app.py)
import os
import json
import random

def create_question_bank(data_dir):
    """ A function to create a question bank for a given split.
    Args:
        data_dir: path to the data files
        split: train, valid, or test
    Returns:
        question_bank: question bank for the given split. Question bank is a list of dictionaries containing keys - 'question', 'answer', 'hints', 'context', 'domain'."""
    # Load the pre-defined question bank from "hintGen/HintGenDataset/quiz_questions.txt" file
    question_bank = json.load(open(os.path.join(data_dir, f"quiz.json"), 'r'))

    # we have 8 physics, 8 biology, 7 chemistry, and 7 earth sciences questions
    question_bank_final = []
    domains = ['physics', 'biology', 'chemistry', 'earth sciences']
    question_domain_dict = {domain: [] for domain in domains}
    for question in question_bank:
        domain = question['domain']
        if domain in question_domain_dict:
            question_domain_dict[domain].append(question)
    # Shuffle the questions within each domain
    for domain in domains:
        random.shuffle(question_domain_dict[domain])
        random.shuffle(question_domain_dict[domain]) # Shuffle again to ensure randomness
    
    # Create the final question bank with specific counts for each section
    section_count = 3
    section_domain_counts = {
        'section_1': {'physics': 3, 'biology': 3, 'chemistry': 2, 'earth sciences': 2},
        'section_2': {'physics': 3, 'biology': 3, 'chemistry': 2, 'earth sciences': 2},
        'section_3': {'physics': 2, 'biology': 2, 'chemistry': 3, 'earth sciences': 3}
    }
    for section in range(1, section_count + 1):
        section_questions = []
        for domain, count in section_domain_counts[f'section_{section}'].items():
            section_questions.extend(question_domain_dict[domain][:count])
            question_domain_dict[domain] = question_domain_dict[domain][count:]
        random.shuffle(section_questions)
        question_bank_final.extend(section_questions)
        
    return question_bank_final