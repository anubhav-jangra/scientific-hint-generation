import os
import uuid
import json
import random
import datetime

import psycopg2
from flask import g

from response_utils import initialize_responses_dict

def get_db_connection():
    """ 
    Get the database connection.
    
    Returns:
        conn: database connection object.
    """

    if 'db_connection' not in g:
        g.db_connection = psycopg2.connect(os.environ.get('DATABASE_URL'))
    return g.db_connection

def close_db_connection(exception=None):
    """ 
    Close the database connection.
    
    Args:
        exception: exception.
        
    Returns:
        None
    """

    db_connection = g.pop('db_connection', None)
    if db_connection is not None:
        db_connection.close()


def init_db():
    """
    A function to initialize the database.
    """

    conn = get_db_connection()
    cur = conn.cursor()

    # # to reset the database
    # cur.execute("TRUNCATE TABLE interactions_v2 RESTART IDENTITY CASCADE")
    # conn.commit()

    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE  table_schema = 'public'
            AND    table_name   = 'interactions_v2'
        )
    """)
    table_exists = cur.fetchone()[0]

    if not table_exists:
        cur.execute("CREATE TABLE interactions_v2 (timestamp TIMESTAMP, participant_id VARCHAR(255), responses JSONB)")
        conn.commit()

    cur.close()

def fetch_old_heroku_data():
    """
    A function to fetch the raw PygreSQL data data from the database.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM interactions")
    rows = cur.fetchall()
    cur.close()

    return rows

def fetch_heroku_data():
    """
    A function to fetch the raw PygreSQL data data from the database.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM interactions_v2")
    rows = cur.fetchall()
    cur.close()

    return rows


def initialize_responses_dict(demographics, question_bank, global_args):
    """ A function to initialize the participant's responses dictionary.
    Args:
        demographics (dict): dictionary containing the participant's demographics.
        question_bank (list of dicts): question bank for the participant.
        global_args (dict): dictionary containing the global arguments.
    Returns:
        participant_id (str): unique id for the participant.
        responses (dict): dictionary containing the participant's responses.
    """

    # assign a unique id to the participant
    participant_id = str(uuid.uuid4())

    # ensure that it is not already present in the database
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM interactions_v2 WHERE participant_id = %s", (participant_id,))
    rows = cur.fetchall()
    while len(rows) > 0:
        participant_id = str(uuid.uuid4())
        cur.execute("SELECT * FROM interactions_v2 WHERE participant_id = %s", (participant_id,))
        rows = cur.fetchall()

    participant_responses = {"Demographics": demographics, "Question Bank": question_bank}

    # initialize the break/resting time dictionary
    participant_responses['breaks'] = {brk_point: {"start_time": None, "end_time": None} for brk_point in global_args['breaks']}

    # initialize the placeholders for the participant's responses
    for inst_idx, inst in enumerate(question_bank):
        question_key = 'question_' + str(inst_idx)
        participant_responses[question_key] = {"question": inst['question'],     # question
                                                "answer": inst['answer'],        # answer
                                                "hints": [],                     # hints asked for
                                                "hint_chain": [],                # hint chain (precomputed for the question based on the strategy order)
                                                "start_time": None,              # start time
                                                "end_time": None,                # end time
                                                "correctly_answered": "no",      # question answered correctly or not
                                                "attempts": 0,                   # total attempts
                                                "attempted_answers": [],         # attempted answers
                                                "action_log": [],                # action log
                                                "survey_responses": []           # survey responses
        }

    # create a random selection strategy order for the question bank (3 strategies - 'no-hint', 'offline', 'online')
    # randomly assign offline/online order first
    if random.random() < 0.5:
        participant_responses['strategy_order'] = ['no-hint']*10 + ['offline']*10 + ['online']*10
    else:
        participant_responses['strategy_order'] = ['no-hint']*10 + ['online']*10 + ['offline']*10

    # update the start time for the first question
    participant_responses['question_0']['start_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # save the participant's responses to the PostgreSQL database
    cur.execute("INSERT INTO interactions_v2 (timestamp, participant_id, responses) VALUES (%s, %s, %s)", 
                (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(participant_id), json.dumps(participant_responses),))
    conn.commit()
    cur.close()

    # temporarily save the participant responses into a json file (for debugging purposes)
    json.dump(participant_responses, open(f"participant_response.json", 'w'), indent=4)

    return participant_id, participant_responses


def update_responses_dict(participant_responses, participant_id, question_key, 
                          add_hint=False, new_hint=None, is_solved=False, wrong_attempt=False, 
                          end_question=False, start_break=False, end_break=False, new_question=False, 
                          attempted_answer=None, action=None, survey_responses=None):
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
    
    elif start_break:
        ques_no = int(question_key.split('_')[-1]) + 1
        participant_responses['breaks'][str(ques_no)]['start_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    elif end_break:
        ques_no = int(question_key.split('_')[-1])
        participant_responses['breaks'][str(ques_no)]['end_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # save the participant's responses to then PostgreSQL before returning it back to the main app
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE interactions_v2 SET responses = %s WHERE participant_id = %s", (json.dumps(participant_responses), participant_id))
    conn.commit()
    cur.close()

    # temporarily save the participant responses into a json file (for debugging purposes)
    json.dump(participant_responses, open(f"participant_response.json", 'w'), indent=4)

    return participant_responses

def load_responses_dict(participant_id):
    """
    A function to load the participant's responses from the database.
    Args:
        participant_id (str): unique id for the participant.
    Returns:
        participant_responses (dict): dictionary containing the participant's responses.
    """
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT responses FROM interactions_v2 WHERE participant_id = %s", (participant_id,))
    rows = cur.fetchall()
    participant_responses = rows[0][0]
    cur.close()

    return participant_responses


def save_response_dict(participant_id, participant_responses):
    """
    A function to save the participant's responses to the database.

    Args:
        participant_id (str): unique id for the participant.
        participant_responses (dict): dictionary containing the participant's responses.
    
    Returns:
        None
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE interactions_v2 SET responses = %s WHERE participant_id = %s", (json.dumps(participant_responses), participant_id))
    conn.commit()
    cur.close()

    # temporarily save the participant responses into a json file (for debugging purposes)
    json.dump(participant_responses, open(f"participant_response.json", 'w'), indent=4)