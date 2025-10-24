# A file to store the utility functions for the responses (storing, loading, updating etc.).

import os
import json
import datetime

def update_participant_id_mapping(mapping_file, participant_id, participant_key):
    """ A function to update the participant id mapping in "responses/participant_id_mapping.json".
    Args:
        mapping_file (str): path to the participant id mapping file.
        participant_id (int): participant id.
        participant_key (str): participant key.
    Returns:
        None
    """

    # update the participant id mapping in "responses/participant_id_mapping.json"
    if os.path.exists(mapping_file): # Load the participant id mapping if it exists
        with open(mapping_file, 'r') as _file:
            participant_id_mapping = json.load(_file)
    else:
        participant_id_mapping = {}

    # update the participant id mapping
    with open(mapping_file, 'w') as _file:
        participant_id_mapping[participant_key] = participant_id
        json.dump(participant_id_mapping, _file)

def initialize_responses_dict(demographics, question_bank):
    """ A function to initialize the participant's responses dictionary.
    Args:
        demographics (dict): dictionary containing the participant's demographics.
        question_bank (list of dicts): question bank for the participant.
    Returns:
        responses (dict): dictionary containing the participant's responses.
    """

    participant_responses = {"Demographics": demographics, "Question Bank": question_bank}

    # initialize the placeholders for the participant's responses
    for idx, inst in enumerate(question_bank):
        question_key = 'question_' + str(idx)
        participant_responses[question_key] = {"question": inst['question'],     # question
                                                "answer": inst['answer'],        # answer
                                                "hints": [],                     # hints asked for
                                                "start_time": None,              # start time
                                                "end_time": None,                # end time
                                                "correctly_answered": "no",      # question answered correctly or not
                                                "attempts": 0,                   # total attempts
                                                "attempted_answers": [],         # attempted answers
                                                "action_log": [],                # action log
                                                "survey_responses": []           # survey responses
        }

    # update the start time for the first question
    participant_responses['question_0']['start_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return participant_responses

def save_responses_dict(participant_responses, participant_id):
    """ A function to save the participant's responses dictionary to a file.
    Args:
        participant_responses (dict): dictionary containing the participant's responses.
        participant_id (int): participant id. Used to store the responses in a file named "responses/{participant_id}.json".
    Returns:
        None
    """
    # save the participant's responses to a file
    with open(f"responses/{participant_id}.json", 'w') as _file:
        json.dump(participant_responses, _file)

def load_responses_dict(participant_id):
    """ A function to load the participant's responses dictionary from a file.
    Args:
        participant_id (int): participant id. Used to load the responses from a file named "responses/{participant_id}.json".
    Returns:
        participant_responses (dict): dictionary containing the participant's responses.
    """
    # load the participant's responses from a file
    with open(f"responses/{participant_id}.json", 'r') as _file:
        participant_responses = json.load(_file)
    return participant_responses

def update_responses_dict(participant_responses, participant_id, question_key, add_hint=False, new_hint=None, is_solved=False, wrong_attempt=False, end_question=False, new_question=False, attempted_answer=None, action=None, survey_responses=None):
    """ A function to update the participant's responses dictionary, and save it to the "responses/{participant_id}.json" file.
    Args:
        participant_responses (dict): dictionary containing the participant's responses.
        question_key (str): key for the question in the responses dictionary.
        add_hint (bool): True if a hint is added, False otherwise.
        end_question (bool): True if the question is ended, False otherwise.
        new_question (bool): True if a new question is started, False otherwise.
    Returns:
        participant_responses (dict): updated dictionary containing the participant's responses.
    """

    # add the hint to the question
    if add_hint:
        participant_responses[question_key]['hints'].append(new_hint)
        participant_responses[question_key]["action_log"].append({"action": "hint requested",
                                                                  "detail": new_hint, 
                                                                  "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    
    # if the question is solved, update the attempts, attempted answers, and the end time
    elif is_solved:
        participant_responses[question_key]["correctly_answered"] = "yes"
        participant_responses[question_key]["end_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        participant_responses[question_key]["attempts"] += 1
        participant_responses[question_key]["attempted_answers"].append(attempted_answer)
        participant_responses[question_key]["action_log"].append({"action": "correct submission",
                                                                  "detail": attempted_answer, 
                                                                  "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    
    # if the question is not solved, update the attempts, attempted answers, and the end time
    elif wrong_attempt:
        participant_responses[question_key]["attempts"] += 1
        participant_responses[question_key]["attempted_answers"].append(attempted_answer)
        participant_responses[question_key]["action_log"].append({"action": "wrong submission",
                                                                  "attempted_answer": attempted_answer, 
                                                                  "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    # update the end time for the question
    elif end_question:
        participant_responses[question_key]['end_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        participant_responses[question_key]["action_log"].append({"action": action,
                                                                  "detail": None,
                                                                  "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    # if a new question is started, update its start time
    elif new_question:
        participant_responses[question_key]['start_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        participant_responses[question_key]["action_log"].append({"action": "stated question",
                                                                  "detail": None,
                                                                  "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    
    elif survey_responses is not None:
        participant_responses[question_key]["survey_responses"] = survey_responses
        participant_responses[question_key]["action_log"].append({"action": "survey completed",
                                                                  "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    # save the participant's responses to a file before returning it back to the main app
    save_responses_dict(participant_responses, participant_id)

    return participant_responses