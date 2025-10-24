import json
import datetime

def get_participant_details_new(participant_data):
    """
    Get the plot utilities for the participant data.
    
    Args:
        participant_data (dict): participant data obtained from the interaction database.
        
    Returns:
        dict: plot utilities for the participant data. (check the dict initialization in the function for more details on the structure of the dict)
    """
    plot_utils = {"total_questions": len(participant_data['Question Bank']),
                  "questions": [question['question'] for question in participant_data['Question Bank']], # a list of questions in the quiz
                  "answers": [question['answer'] for question in participant_data['Question Bank']], # a list of answers to the questions in the quiz
                  "domain": [0] * len(participant_data['Question Bank']), # a list to store the domain of each question
                  "correctly_answered": [0] * len(participant_data['Question Bank']), # a list to store whether the question was correctly answered or not
                  "total_attempts": [], # a list to store the total attempts made by the participant on each question
                  "time_taken": [], # a list to store the time taken by the participant to answer each question
                  "hint_strategies": participant_data['strategy_order'],
                  "actions": [], # a list of lists to store the actions for each question
                  "hints": [], # a list of lists to store the hints shown to the participant for each question
                  "attempted_answers": [], # a list of lists to store the attempted answers for each question
                  "total_time": "00:00:00", # total time taken by the participant to finish the quiz. 00:00:00 denotes that the user didn't finish the quiz.
                  "total_correct_answers": 0, # total number of questions correctly answered by the participant
                  "start_times": [], # a list of start times for each question
                  "end_times": [], # a list of end times for each question
                  "total_time_spent": [], # a list of total time spent by the participant on each question
                #   "subject_confidence": {domain: int(participant_data['Demographics'][domain][0]) for domain in ['physics', 'chemistry', 'biology', 'earth_sciences']}, # self-reported subject confidence
                  "subject_confidence": {domain: int(participant_data['subject_confidence'][domain]) for domain in ['physics', 'chemistry', 'biology', 'earth_sciences']}, # self-reported subject confidence
                  "survey_responses": [participant_data['question_' + str(q_no)]['survey_responses'] for q_no in range(len(participant_data['Question Bank']))], # survey responses given by the participant
                  "skipped_question": [1 if "gave up the question" in [action['action'] for action in participant_data['question_' + str(q_no)]['action_log']] else 0 for q_no in range(len(participant_data['Question Bank']))], # a list to store whether the question was skipped or not
                  "exhausted_attemps": [1 if "exhausted attempts" in [action['action'] for action in participant_data['question_' + str(q_no)]['action_log']] else 0 for q_no in range(len(participant_data['Question Bank']))], # a list to store whether the question was skipped or not
    }

    # iterate over all the questions in the participant data to obtain the question-level utilities
    for question_id in range(plot_utils["total_questions"]):

        # get the key for the question in the participant data
        question_key = 'question_' + str(question_id)
        question_data = participant_data[question_key]

        plot_utils["total_attempts"].append(question_data['attempts'])
        plot_utils["correctly_answered"][question_id] = 1 if question_data['correctly_answered'] == 'yes' else 0

        if question_data['end_time'] is None:
            plot_utils["time_taken"].append("00:00:00")
        else:
            plot_utils["time_taken"].append(get_time_difference(question_data['end_time'], question_data['start_time']))
        
        plot_utils["actions"].append(question_data['action_log'])
        plot_utils["hints"].append(question_data['hints'])
        plot_utils["attempted_answers"].append(question_data['attempted_answers'])
        
        # fetch the domain information from the question bank
        plot_utils["domain"][question_id] = [question for question in participant_data['Question Bank'] if question['question'] == question_data['question']][0]['domain']

        # update the start and end times for the question
        plot_utils["start_times"].append(question_data['start_time'])
        plot_utils["end_times"].append(question_data['end_time'])
        # update the total time spent by the participant on the question
        if question_data['end_time'] is None:
            question_data['end_time'] = participant_data[question_key]['action_log'][-1]['timestamp']
        plot_utils["total_time_spent"].append(min(get_time_difference(question_data['end_time'], question_data['start_time']), 1800))
    
    # compute the quiz-level utilities for the participant
    plot_utils["total_correct_answers"] = sum(plot_utils["correctly_answered"])
    if participant_data['question_29']['end_time'] is not None:
        plot_utils["total_time"] = get_time_difference(participant_data['question_29']['end_time'], participant_data['question_0']['start_time'])
    
    plot_utils["question_domain_mapping"] = {'A metarteriole is a type of vessel that has structural characteristics of both an arteriole and this?': 'biology',
                                            'A vector is an organism that carries what disease-causing microorganisms from one person or animal to another?': 'biology',
                                            'Algae produce food using what process?': 'biology',
                                            'Candida and trichophyton are examples of disease-causing types of what organisms, which become parasitic?': 'biology',
                                            'Carpal, metacarpal and phalanx bones comprise what part of the body?': 'biology',
                                            'Cells that have a nucleus and other organelles which are membrane-bound are generally called what kinds of cells?': 'biology',
                                            'How do many mammals control their body temperature?': 'biology',
                                            'Hepatitis b is inflammation of which organ?': 'biology',
                                            'A skydiver will reach what when the air drag equals their weight?': 'physics',
                                            'Electricity consists of a constant stream of what tiny particles?': 'physics',
                                            'In relation to electrical current, what property will a narrow wire have more of than a wide wire?': 'physics',
                                            'Light is a form of what kind of energy?': 'physics',
                                            'Radioactive atoms, nuclear explosions, and stars produce what types of rays.': 'physics',
                                            'The amount of heat required to raise a single mass unit of a substance by a single temperature unit is known as what?': 'physics',
                                            'The efficiency of a machine is a measure of how well it reduces what force?': 'physics',
                                            'What is the term for the ability of a fluid to exert an upward force on any object placed in it?': 'physics',
                                            'Chemical reactions involve a transfer of heat energy. measured in what?': 'chemistry',
                                            'Pure carbon can exist in different forms, depending on how its atoms are arranged. the forms include diamond, graphite, and what else?': 'chemistry',
                                            'Salicylic acid is used in the synthesis of acetylsalicylic acid, or more commonly called?': 'chemistry',
                                            'The bohr model works only for which atom?': 'chemistry',
                                            'The energy required to remove an electron from a gaseous atom is called?': 'chemistry',
                                            'The strength of a base depends on the concentration of _______ it produces when dissolved in water?': 'chemistry',
                                            'What are atoms of the same element that differ in their numbers of neutrons called?': 'chemistry',
                                            'Farming practices leave some soil exposed and vulnerable to what natural process?': 'earth science',
                                            'What are gases called that absorb heat in the atmosphere?': 'earth science',
                                            'What are located along convergent and divergent plate boundaries?': 'earth science',
                                            'What gas is released when dead organisms and other organic materials decompose?': 'earth science',
                                            'What is land with permafrost, no trees, and small hardy plants?': 'earth science',
                                            "What is the most abundant metal of the earth's crust?": 'earth science',
                                            'What type of rocks form when an existing rock is changed by heat or pressure?': 'earth science',
    }

    # add miscellaneous domain to subject confidence scores
    plot_utils["subject_confidence"]["miscellaneous"] = 0

    return plot_utils

def get_participant_details(participant_data):
    """
    Get the plot utilities for the participant data.
    
    Args:
        participant_data (dict): participant data obtained from the interaction database.
        
    Returns:
        dict: plot utilities for the participant data. (check the dict initialization in the function for more details on the structure of the dict)
    """
    plot_utils = {"total_questions": len(participant_data['Question Bank']),
                  "questions": [question['question'] for question in participant_data['Question Bank']], # a list of questions in the quiz
                  "answers": [question['answer'] for question in participant_data['Question Bank']], # a list of answers to the questions in the quiz
                  "domain": [0] * len(participant_data['Question Bank']), # a list to store the domain of each question
                  "correctly_answered": [0] * len(participant_data['Question Bank']), # a list to store whether the question was correctly answered or not
                  "total_attempts": [], # a list to store the total attempts made by the participant on each question
                  "time_taken": [], # a list to store the time taken by the participant to answer each question
                  "hint_strategies": participant_data['strategy_order'],
                  "actions": [], # a list of lists to store the actions for each question
                  "hints": [], # a list of lists to store the hints shown to the participant for each question
                  "attempted_answers": [], # a list of lists to store the attempted answers for each question
                  "total_time": "00:00:00", # total time taken by the participant to finish the quiz. 00:00:00 denotes that the user didn't finish the quiz.
                  "total_correct_answers": 0, # total number of questions correctly answered by the participant
                  "start_times": [], # a list of start times for each question
                  "end_times": [], # a list of end times for each question
                  "total_time_spent": [], # a list of total time spent by the participant on each question
                  "subject_confidence": {domain: int(participant_data['Demographics'][domain][0]) for domain in ['physics', 'chemistry', 'biology', 'earth_sciences']}, # self-reported subject confidence
                  "survey_responses": [participant_data['question_' + str(q_no)]['survey_responses'] for q_no in range(len(participant_data['Question Bank']))], # survey responses given by the participant
                  "remarks_responses": participant_data['remarks'], # remarks responses given by the participant
                  "skipped_question": [1 if "gave up the question" in [action['action'] for action in participant_data['question_' + str(q_no)]['action_log']] else 0 for q_no in range(len(participant_data['Question Bank']))], # a list to store whether the question was skipped or not
                  "exhausted_attemps": [1 if "exhausted attempts" in [action['action'] for action in participant_data['question_' + str(q_no)]['action_log']] else 0 for q_no in range(len(participant_data['Question Bank']))], # a list to store whether the question was skipped or not
    }
    # if section survey in the participant data, add it to the plot utilities
    if 'section_survey_1' in participant_data:
        plot_utils["section_survey_responses"] = [participant_data[f'section_survey_{idx}'] for idx in range(1, 4)] # section survey responses given by the participant

    # iterate over all the questions in the participant data to obtain the question-level utilities
    for question_id in range(plot_utils["total_questions"]):

        # get the key for the question in the participant data
        question_key = 'question_' + str(question_id)
        question_data = participant_data[question_key]

        plot_utils["total_attempts"].append(question_data['attempts'])
        plot_utils["correctly_answered"][question_id] = 1 if question_data['correctly_answered'] == 'yes' else 0

        if question_data['end_time'] is None:
            plot_utils["time_taken"].append("00:00:00")
        else:
            plot_utils["time_taken"].append(get_time_difference(question_data['end_time'], question_data['start_time']))
        
        plot_utils["actions"].append(question_data['action_log'])
        plot_utils["hints"].append(question_data['hints'])
        plot_utils["attempted_answers"].append(question_data['attempted_answers'])
        
        # fetch the domain information from the question bank
        plot_utils["domain"][question_id] = [question for question in participant_data['Question Bank'] if question['question'] == question_data['question']][0]['domain']

        # update the start and end times for the question
        plot_utils["start_times"].append(question_data['start_time'])
        plot_utils["end_times"].append(question_data['end_time'])
        # update the total time spent by the participant on the question
        plot_utils["total_time_spent"].append(get_time_difference(question_data['end_time'], question_data['start_time']))
    
    # compute the quiz-level utilities for the participant
    plot_utils["total_correct_answers"] = sum(plot_utils["correctly_answered"])
    if participant_data['question_29']['end_time'] is not None:
        plot_utils["total_time"] = get_time_difference(participant_data['question_29']['end_time'], participant_data['question_0']['start_time'])
    
    plot_utils["question_domain_mapping"] = {'A metarteriole is a type of vessel that has structural characteristics of both an arteriole and this?': 'biology',
                                            'A vector is an organism that carries what disease-causing microorganisms from one person or animal to another?': 'biology',
                                            'Algae produce food using what process?': 'biology',
                                            'Candida and trichophyton are examples of disease-causing types of what organisms, which become parasitic?': 'biology',
                                            'Carpal, metacarpal and phalanx bones comprise what part of the body?': 'biology',
                                            'Cells that have a nucleus and other organelles which are membrane-bound are generally called what kinds of cells?': 'biology',
                                            'How do many mammals control their body temperature?': 'biology',
                                            'Hepatitis b is inflammation of which organ?': 'biology',
                                            'A skydiver will reach what when the air drag equals their weight?': 'physics',
                                            'Electricity consists of a constant stream of what tiny particles?': 'physics',
                                            'In relation to electrical current, what property will a narrow wire have more of than a wide wire?': 'physics',
                                            'Light is a form of what kind of energy?': 'physics',
                                            'Radioactive atoms, nuclear explosions, and stars produce what types of rays.': 'physics',
                                            'The amount of heat required to raise a single mass unit of a substance by a single temperature unit is known as what?': 'physics',
                                            'The efficiency of a machine is a measure of how well it reduces what force?': 'physics',
                                            'What is the term for the ability of a fluid to exert an upward force on any object placed in it?': 'physics',
                                            'Chemical reactions involve a transfer of heat energy. measured in what?': 'chemistry',
                                            'Connecting a magnesium rod to an underground steel pipeline protects the pipeline from corrosion. because magnesium (e° = −2.37 v) is much more easily oxidized than iron (e° = −0.45 v), the mg rod acts as the anode in a what?': 'chemistry',
                                            'Pure carbon can exist in different forms, depending on how its atoms are arranged. the forms include diamond, graphite, and what else?': 'chemistry',
                                            'Salicylic acid is used in the synthesis of acetylsalicylic acid, or more commonly called?': 'chemistry',
                                            'The bohr model works only for which atom?': 'chemistry',
                                            'The energy required to remove an electron from a gaseous atom is called?': 'chemistry',
                                            'The strength of a base depends on the concentration of _______ it produces when dissolved in water?': 'chemistry',
                                            'What are atoms of the same element that differ in their numbers of neutrons called?': 'chemistry',
                                            'Farming practices leave some soil exposed and vulnerable to what natural process?': 'earth science',
                                            'What are gases called that absorb heat in the atmosphere?': 'earth science',
                                            'What are located along convergent and divergent plate boundaries?': 'earth science',
                                            'What do concentric circles on a topographic map indicate?': 'earth science',
                                            'What gas is released when dead organisms and other organic materials decompose?': 'earth science',
                                            'What is land with permafrost, no trees, and small hardy plants?': 'earth science',
                                            "What is the most abundant metal of the earth's crust?": 'earth science',
                                            'What type of rocks form when an existing rock is changed by heat or pressure?': 'earth science',
    }

    # add miscellaneous domain to subject confidence scores
    plot_utils["subject_confidence"]["miscellaneous"] = 0

    return plot_utils

def get_time_difference(str1, str2):
    """
    Get the time difference between two timestamps in string format (YYYY-MM-DD HH:MM:SS).

    Args:
        str1 (str): timestamp string 1.
        str2 (str): timestamp string 2.

    Returns:
        int: time difference in seconds.
    """
    time1 = datetime.datetime.strptime(str1, "%Y-%m-%d %H:%M:%S")
    time2 = datetime.datetime.strptime(str2, "%Y-%m-%d %H:%M:%S")
    return abs((time2 - time1).total_seconds())

def save_filtered_data(data, out_file_name):
    """
    Save the data to a file. 
    Filter out test instances from the dataset, and anonymize the data.
    
    Args:
        data (list of tuples): data to be saved.
        out_file_name (str): name of the file to save the data.
    
    Returns:
        response_data (dict): filtered data that is saved to the out_file_name path.
    """ 
    response_data = {}

    for inst in data:
        # check if the participant is a test participant, otherwise skip
        if 'Demographics' not in inst[2]:
            continue
        if 'test' in inst[2]['Demographics']['name'].lower() or 'test' in inst[2]['Demographics']['email'].lower():
            continue
            
        # check if the participant finished the quiz, otherwise skip
        if inst[2]['question_29']['end_time'] is None:
            continue
        
        participant_id = 'P-' + str(len(response_data))
        response_data[participant_id] = inst[2]
        response_data[participant_id]['begin_time'] = inst[0].strftime("%Y-%m-%d %H:%M:%S")

    if out_file_name is not None:
        with open(out_file_name, 'w') as f:
            f.write(json.dumps(response_data, indent=4))

    return response_data

def get_info_score(question_hint_similarities, answer_hint_similarities, answer, _threshold=0.9):
    """
    A function to calculate the informativeness score for a given instance.

    Args:
        question_hint_similarities (dict) : question-hint similarities
        answer_hint_similarities (dict)   : answer-hint similarities
        _threshold (float)                : threshold value to ensure that hint is not too close to question or answer

    Returns:
        info_score (dict)                  : informativeness score for each hint
    """
    info_score = {}

    for hint in question_hint_similarities:
        # check if answer is present in the hint
        if answer.lower() in hint.lower():
            info_score[hint] = 1.0
            continue
        # check if hint is too close to question or answer
        if question_hint_similarities[hint] >= _threshold:
            info_score[hint] = 1 - question_hint_similarities[hint]
        elif answer_hint_similarities[hint] >= _threshold:
            info_score[hint] = answer_hint_similarities[hint]
        else:
            # I = ((1-q) + a) / 2
            info_score[hint] = (1 - question_hint_similarities[hint] + answer_hint_similarities[hint]) / 2
    return info_score