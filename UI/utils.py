# File containing utility functions for hintGen UI codebase.

import os
import ast
import json
import random

from openai import OpenAI

def check_answer(question, attempted_answer, correct_answer, _model='gpt-3.5-turbo'):
    """ A function to check if the attempted answer is correct.
    Args:
        question (str): question.
        attempted_answer (str): attempted answer.
        correct_answer (str): correct answer.
        _model (str): a string that can take values 'gpt-4', 'gpt-3.5-turbo', 'gpt-4o-mini'
    Returns:
        result (bool): True if the attempted answer is correct, False otherwise.
    """
    # do an exact match first
    if attempted_answer.strip().lower() == correct_answer.strip().lower():
        return True
    
    # Make use of a GPT call to check if the answer is correct.
    # Load the client for OpenAI models
    # Replace "os.environ['OPENAI_API_KEY']" with your OpenAI API key
    client = OpenAI(
        api_key=os.environ['OPENAI_API_KEY'],
    )

    _prompt = f"""You are given a question, correct answer, and an attempted answer.
Determine if the attempted answer is correct or not. If the attempted answer semantically matches the correct answer, then return "correct", otherwise "incorrect".
    
Question: {question}
Correct Answer: {correct_answer}
Attempted Answer: {attempted_answer}
Is the attempted answer correct or not? - """

    counter = 0
    response = 'ERROR OCCURRED!'
    while counter < 20 and response == 'ERROR OCCURRED!':
        try:
            counter += 1
            chat = client.chat.completions.create(
                model=_model,
                messages=[{"role": "user", "content": _prompt}]
            )
            response = chat.choices[0].message.content
        except Exception as e:
            response = 'ERROR OCCURRED!'
            print('Error occured:', e)
    
    if response == 'correct':
        return True
    else:
        return False

def get_html_survey_from_hints(hints, participant_id, question_number):
    """ A function to convert the hints to an HTML survey.
    Args:
        hints (list of str)     : list of hints.
        participant_id (int)    : participant id. (Passed as a hidden input in the survey form.)
        question_number (int)   : question id. (Passed as a hidden input in the survey form.)
    Returns:
        html_survey (str): HTML formatted survey.
    """
    html = '<form action = "/survey" method = "POST">\n'
    
    # add a hidden input to pass the participant_id and question_id
    html += f'<input type="hidden" id="participant_id" name="participant_id" value="{participant_id}">\n'
    html += f'<input type="hidden" id="question_number" name="question_number" value="{question_number}">\n'

    # add the hints to the survey
    for i, hint in enumerate(hints):
        html += f'<br><label for="hint{i}"><b>Hint {i+1}:</b> {hint}</label><br><br>\n'
        html += f'<div class="radio-buttons">'
        html += f'<input type="radio" name="hint{i}" value="1" required> Very Dissatisfied\n'
        html += f'<input type="radio" name="hint{i}" value="2"> Dissatisfied\n'
        html += f'<input type="radio" name="hint{i}" value="3"> Neutral\n'
        html += f'<input type="radio" name="hint{i}" value="4"> Satisfied\n'
        html += f'<input type="radio" name="hint{i}" value="5"> Very Satisfied<br><br>\n'
        html += f'</div>'
    
    html += '<hr style="border: none; border-top: 2px solid gray; color: gray; overflow: visible; text-align: center; height: 5px;">\n'
    html += "<p><b>Did you learn something new from the hints?</b></p>\n"
    for i, hint in enumerate(hints):
        html += f'<br><label for="informativeness{i}"><b>Hint {i+1}:</b> {hint}</label><br><br>\n'
        html += f'<input type="radio" name="informativeness{i}" value="Yes" required> Yes\n'
        html += f'<input type="radio" name="informativeness{i}" value="No"> No<br><br>\n'

    html += '<hr style="border: none; border-top: 2px solid gray; color: gray; overflow: visible; text-align: center; height: 5px;">\n'
    html += "<p><b>Does the hint directly give away the answer?</b></p>\n"
    for i, hint in enumerate(hints):
        html += f'<br><label for="leakage{i}"><b>Hint {i+1}:</b> {hint}</label><br><br>\n'
        html += f'<input type="radio" name="leakage{i}" value="Yes" required> Yes\n'
        html += f'<input type="radio" name="leakage{i}" value="No"> No<br><br>\n'

    # add the submit button
    html += '<input type="submit" value="Submit" class="submit-button">\n'
    html += '</form>'

    return html

def get_questions_html():
    """
    A function to obtain HTML text to populate question options in the plots webpage
    
    Args:
        None
    
    Returns:
        (str) : HTML string of question options
    """
    # a file with \n separated questions
    question_file_path = "hintGen/quiz_data/quiz.json"

    quiz_data = json.load(open(question_file_path, 'r'))
    questions = [inst['question'] for inst in quiz_data]
    
    html = ""
    for ques in questions:
        html += f"""<option value="{ques}">{ques}</option>"""
    
    return html