from flask import render_template

from response_utils_db import update_responses_dict
from utils import get_html_survey_from_hints

def get_progress_bar_html(question_number, total_questions, checkpoints=[]):
    """ A function to get the progress bar HTML.
    Args:
        question_number (int): question number.
        total_questions (int): total number of questions.
        checkpoints (list): list of question numbers where checkpoints should be placed.
    Returns:
        progress_bar_html (HTML): HTML for the progress bar.
    """
    progress_bar_width = round((question_number + 1) / total_questions * 100, 2)
    checkpoint_html = ""
    for checkpoint in checkpoints:
        checkpoint_position = round((checkpoint) / total_questions * 100, 2)
        checkpoint_html += f"""<div class="checkpoint" style="left: {checkpoint_position}%;"></div>"""

    progress_bar_html = f"""
    <div class="progress-container">
        <div class="progress">
            <div class="progress-bar" role="progressbar" style="width: {progress_bar_width}%;" aria-valuenow="{progress_bar_width}" aria-valuemin="0" aria-valuemax="100">
                <span id="progress-text"></span>
            </div>
            {checkpoint_html}
        </div>
    </div>
    """
    return progress_bar_html

def get_alert_message(message, is_good=True):
    """ A function to get the alert message HTML.
    Args:
        message (str):  message to display.
        is_good (bool): True if the message is positive, False otherwise.
    Returns:
        alert_message_html (HTML): HTML for the alert message.
    """
    if message is None or message == "":
        return ""
    
    color = "#30945d" if is_good else "#8d2c25"
    alert_message_html = f"""<div class="alert" style="background-color: {color}">
                                <span class="closebtn" onclick="this.parentElement.style.display='none';">&times;</span>
                                {message}
                            </div>"""
    return alert_message_html


def get_attempts_left(attempts_left):
    """ A function to get the attempts left HTML.
    Args:
        attempts_left (int): number of attempts left.
    Returns:
        attempts_left_html (HTML): HTML for the attempts left.
    """
    attempts_left_html = """<span class="life"></span>\n""" * attempts_left
    return attempts_left_html


def get_hint_str(hint):
    """ A function to get the hint string for the typewriter effect. 
    Break down the hint with '\n' separators and join the words with a space.
    Args:
        hint (str): hint.
    Returns:
        hint_str (str): hint string.
    """
    hint_arr = hint.split()
    hint_str = ""
    for idx, word in enumerate(hint_arr):
        if idx != 0 and idx % 10 == 0:
            hint_str += "\n"
        hint_str += word + " "
    print(hint_str)
    return hint_str


def get_piechart_html(correct_answers, total_questions):
    """ A function to get the pie chart HTML.
    Args:
        correct_answers (int): number of correct answers.
        total_questions (int): total number of questions.
    Returns:
        piechart_html (HTML): HTML for the pie chart.
    """
    correct_angle = correct_answers/total_questions*360
    piechart_html = f"""style="background-image: conic-gradient(
        #67ac69 0 {int(correct_angle)}deg,
        #d85248 0);" """
    return piechart_html


def get_qa_pairs_html(participant_responses, section_no=None):
    """ A function to get the QA pairs HTML.
    Args:
        participant_responses (dict): dictionary containing the participant's responses.
        section_no (int): section number. If None, all sections are shown. Otherwise, questions from the specified section are shown.
    Returns:
        qa_pairs_html (HTML): HTML for the QA pairs.
    """
    question_bank = participant_responses['Question Bank']

    def get_hints_shown(idx):
        question_key = 'question_' + str(idx)
        hints_shown = participant_responses[question_key]["hints"] if len(participant_responses[question_key]["hints"]) > 0 else "No hints shown."
        if hints_shown == "No hints shown.":
            return str(hints_shown) + "<br>"
        else:
            hints_list_html = "<b>Hints:</b><ul>"
            for hint in hints_shown:
                hints_list_html += "<li>" + hint + "</li>"
            hints_list_html += "</ul>"
            return str(hints_list_html)
    def get_user_attempts(idx):
        question_key = 'question_' + str(idx)
        attempts = participant_responses[question_key]["attempted_answers"]
        return str(attempts) if len(attempts) > 0 else "No attempts made."

    if section_no is None:
        question_bank_subset = question_bank
    elif section_no == 1:
        question_bank_subset = question_bank[:10]
    elif section_no == 2:
        question_bank_subset = question_bank[10:20]
    elif section_no == 3:
        question_bank_subset = question_bank[20:]
    else:
        raise ValueError("Invalid section number. Must be 1, 2, or 3, or None to show all sections.")

    qa_pairs_html = "<ul>"
    for idx, inst in enumerate(question_bank_subset):
        qa_pairs_html += "<li>"
        qa_pairs_html += "<b>Question:</b> " + inst['question'] + "<br>"
        qa_pairs_html += "<b>Correct Answer:</b> " + inst['answer'] + "<br>"
        qa_pairs_html += "<b>Your attempts:</b> " + get_user_attempts(idx) + "<br>" if section_no is None else "<b>Your attempts:</b> " + get_user_attempts(idx + (section_no - 1) * 10) + "<br>"
        qa_pairs_html += "<b>Hint(s) Used:</b> " + get_hints_shown(idx) if section_no is None else get_hints_shown(idx + (section_no - 1) * 10)
        if section_no is None:
            qa_pairs_html += "<b>Domain:</b> " + inst['domain'] + "<br>"
        qa_pairs_html += "</li><br>"
    qa_pairs_html += "</ul>"
    return qa_pairs_html

def show_past_hints(participant_responses, question_number):
    """
    A function to obtain the HTML for the hints that were asked for a question so far.
    Args:
        participant_responses (dict): dictionary containing the participant's responses.
        question_number (int): question number.
    Returns:
        hints_html (HTML): HTML for the hints that were asked for a question so far.
    """
    hints_html = """<details>
                        <summary>Click to view past hints</summary>"""
    question_key = 'question_' + str(question_number)
    hints = participant_responses[question_key]["hints"]
    if len(hints) == 0:
        hints_html += "<p>No hints asked for this question yet.</p>"
    else:
        hints_html += "<ul>"
        for hint in hints:
            hints_html += "<li>" + hint + "</li>"
        hints_html += "</ul>"
    hints_html += "</details>"
    return hints_html


def load_same_page(participant_responses, participant_id, question_number, global_args, render_hint=None, message=None, good_message=True):
    """ A function to load the same page of data as question_number.
    Args:
        participant_responses (dict): dictionary containing the participant's responses.
        participant_id (str): participant's ID.
        question_number (int): question number.
        global_args (dict): dictionary containing global arguments.
        render_hint (str): hint to render on the page. If not None, the function assumes hint was requested.
        message (str): message to display on the page.
        good_message (bool): True if the message is positive, False otherwise. Used to determine the alert color.
    Returns:
        page (HTML): HTML page to render.
    """
    question_key = 'question_' + str(question_number)
    question_bank = participant_responses['Question Bank']
    
    # if the message is NOTHING (i.e., no message), render the same question without any message
    # This comes from the case when the participant seeks to view past hints
    show_hint_button = False if participant_responses['strategy_order'][question_number] == 'no-hint' else True
    if message == "NOTHING":
        # return the quiz.html page with the same question
        return render_template('quiz.html',
                                participant_id=participant_id, 
                                question_number=question_number, 
                                question=question_bank[question_number]['question'], 
                                progress=question_number+1, 
                                progress_bar_width=get_progress_bar_html(question_number, len(question_bank), global_args['breaks']),
                                attempts_left=get_attempts_left(global_args['total_attempts'] - participant_responses[question_key]["attempts"]), 
                                total_questions=len(question_bank),
                                show_hint_button=show_hint_button,
                                show_hints=show_past_hints(participant_responses, question_number),
        )

    # if "Want Hint?" button is clicked, render the survey page with the hints
    if render_hint is not None:
        # return the quiz.html page with the question and the best hint
        return render_template('quiz.html', 
                                participant_id=participant_id, 
                                question_number=question_number, 
                                question=question_bank[question_number]['question'], 
                                hint=' '.join(render_hint.split()), 
                                progress=question_number+1, 
                                progress_bar_width=get_progress_bar_html(question_number, len(question_bank), global_args['breaks']),
                                attempts_left=get_attempts_left(global_args['total_attempts'] - participant_responses[question_key]["attempts"]), 
                                total_questions=len(question_bank),
                                show_hint_button=show_hint_button,
                                show_hints=show_past_hints(participant_responses, question_number),
        )
    
    # otherwise, a failed attempt was made. Render the same question with a message
    else:
        # return the quiz.html page with the same question and a message passed in the argument {message}
        return render_template('quiz.html', 
                            participant_id=participant_id, 
                            question_number=question_number, 
                            question=question_bank[question_number]['question'], 
                            progress=question_number+1,
                            progress_bar_width=get_progress_bar_html(question_number, len(question_bank), global_args['breaks']),
                            total_questions=len(question_bank),
                            attempts_left=get_attempts_left(global_args['total_attempts'] - participant_responses[question_key]["attempts"]),
                            alert_message=get_alert_message(message, good_message),
                            show_hint_button=show_hint_button,
                            show_hints=show_past_hints(participant_responses, question_number),
        )


def load_next_page(participant_responses, participant_id, question_number, global_args, check_for_survey=False, message="No message!", good_message=True):
    """ A function to load the next page of data. This function checks if we need to render the survey page, and if the quiz is over.
    Args:
        participant_responses (dict): dictionary containing the participant's responses.
        participant_id (str): participant's ID.
        question_number (int): question number.
        global_args (dict): dictionary containing global arguments.
        check_for_survey (bool): True if we need to check for survey, False otherwise.
        message (str): message to display on the page.
        good_message (bool): True if the message is positive, False otherwise. Used to determine the alert color.
    Returns:
        page (HTML): HTML page to render.
    """

    question_key = 'question_' + str(question_number)
    question_bank = participant_responses['Question Bank']

    # check if we need to render the survey page
    if check_for_survey:
        # check if hints were used for the question and render the survey page if they were
        if len(participant_responses[question_key]["hints"]) > 0:
            # convert the hints into an HTML survey
            survey_html = get_html_survey_from_hints(participant_responses[question_key]["hints"], participant_id, question_number)
            # return the survey.html page with the hints
            return render_template('survey.html', 
                                    participant_id=participant_id, 
                                    question_number=question_number, 
                                    question=question_bank[question_number]['question'],
                                    answer=question_bank[question_number]['answer'],
                                    hints_form=survey_html)

    print("Question number:", question_number)
    # check if the next page is a break/resting page # AJ: updated this to directly go to the section survey page (lazy logic)
    if question_number+1 in global_args['breaks']:
        # # check if the break has not started yet
        if participant_responses['breaks'][str(question_number+1)]['start_time'] is None:
            # update the start time for the break
            participant_responses = update_responses_dict(participant_responses, participant_id, question_key, start_break=True)
            # return the break.html page
            return render_template('section_survey.html', 
                                    participant_id=participant_id,
                                    question_number=question_number,
                                    progress=question_number+1,
                                    progress_bar_width=get_progress_bar_html(question_number, len(participant_responses['Question Bank']), global_args['breaks']),
                                    total_questions=len(participant_responses['Question Bank']),
                                    section_number={10: 1, 20: 2, 30: 3}[question_number+1],
                                    show_hint_ques=False if question_number+1 == 10 else True,
            )

    # check if the quiz is over
    if question_number >= len(participant_responses['Question Bank']) - 1:
        section_info_revealing_str = ""
        if participant_responses['strategy_order'][11] == 'offline': # section 2 is offline, section 3 is online
            section_info_revealing_str = "Hints presented in Section 2 were a pre-determined set of suggestions. <br>Hints presented in Section 3 were designed to be adaptive to your previous attempt for the question."
        else:
            section_info_revealing_str = "Hints presented in Section 3 were a pre-determined set of suggestions. <br>Hints presented in Section 2 were designed to be adaptive to your previous attempt for the question."
        return render_template('remarks.html',
                               participant_id=participant_id,
                               section_info_revealing_str=section_info_revealing_str,
                               qa_pairs_html_section_1=get_qa_pairs_html(participant_responses, section_no=1),
                               qa_pairs_html_section_2=get_qa_pairs_html(participant_responses, section_no=2),
                               qa_pairs_html_section_3=get_qa_pairs_html(participant_responses, section_no=3)
        )
    else:
        # update the start time for the next question
        participant_responses = update_responses_dict(participant_responses, participant_id, 'question_' + str(question_number+1), new_question=True)

        # check if the next question is a part of the no-hint section
        show_hint_button = False if participant_responses['strategy_order'][question_number+1] == 'no-hint' else True
        # return the quiz.html page with the next question
        return render_template('quiz.html', 
                                participant_id=participant_id, 
                                question_number=question_number+1, 
                                question=participant_responses['Question Bank'][question_number+1]['question'], 
                                progress=question_number+2, 
                                progress_bar_width=get_progress_bar_html(question_number+1, len(participant_responses['Question Bank']), global_args['breaks']),
                                total_questions=len(participant_responses['Question Bank']), 
                                attempts_left=get_attempts_left(global_args['total_attempts']), 
                                alert_message=get_alert_message(message, good_message), 
                                show_hint_button=show_hint_button,
                                show_hints="",
            )

def load_thank_you_page(participant_responses, participant_id):
    """
    A function to load the thank you page.
    Args:
        participant_responses (dict): dictionary containing the participant's responses.
        participant_id (str): participant's ID.
    Returns:
        page (HTML): HTML page to render.
    """
    # obtain the statistics for the quiz taken by the participant
    correct_answers, total_questions, total_hints_asked, average_hint_rating = obtain_stats_for_quiz(participant_responses)
    # return the quiz.html page with the end time and a message that the quiz is over
    return render_template('thank_you.html', 
                            correct_answers=correct_answers, 
                            total_questions=total_questions, 
                            total_hints_asked=total_hints_asked, 
                            average_hint_rating="{:.2f}".format(average_hint_rating),
                            piechart_html=get_piechart_html(correct_answers, total_questions),
                            qa_pairs_html=get_qa_pairs_html(participant_responses),
    )

def obtain_stats_for_quiz(participant_responses):
    """ A function to obtain the statistics for the quiz taken by the participant.
    Args:
        participant_responses (dict): dictionary containing the participant's responses.
    Returns:"""
    # obtain the statistics for the quiz taken by the participant
    correct_answers = 0
    total_questions = len(participant_responses['Question Bank'])
    total_hints_asked = 0
    total_hint_rating = 0

    for question_key in participant_responses.keys():
        if 'question_' in question_key:
            # calculate the number of correct answers
            if participant_responses[question_key]['correctly_answered'] == "yes":
                correct_answers += 1

            # calculate the number of hints asked
            total_hints_asked += len(participant_responses[question_key]['hints'])

            # calculate the total hint rating
            for responses in participant_responses[question_key]["survey_responses"]:
                total_hint_rating += int(responses['response'])

    # calculate the average hint rating
    if total_hints_asked == 0:
        average_hint_rating = 0
    else:
        average_hint_rating = total_hint_rating / total_hints_asked

    return correct_answers, total_questions, total_hints_asked, average_hint_rating