import json
import datetime

from flask import Flask, request, render_template

from data_utils import create_question_bank
from app_utils import load_same_page, load_next_page, load_thank_you_page, get_qa_pairs_html
from response_utils_db import init_db, load_responses_dict, save_response_dict, initialize_responses_dict, update_responses_dict, fetch_heroku_data, fetch_old_heroku_data
from utils import check_answer, get_questions_html
from Plots.my_plots import obtain_plot, generate_all_plots

from hintGen.custom_hints import generate_custom_hints
from hintGen.prompt_funcs import get_offline_hint, get_online_hint

# Global variables
global_args = {'hintGen_data_dir': "./hintGen/quiz_data",
                'total_attempts': 5, # the total attempts allowed for each question
                'hint_selection_strategies': {'offline': get_offline_hint, 'online': get_online_hint},
                'hint_selection_desc': {'offline': "Predetermined hints.",
                                        'online': "Adaptively generated hints based on the past responses and hints shown."},
                'participant_file_mapping_path': 'responses/participant_id_mapping.json',
                'breaks': [10, 20, 30] # hardcoded breaks/section ends for a 30 question quiz (10-10-10 sections)
               }

# Load the Flask app
app = Flask(__name__)

# Initialize the database
with app.app_context():
    init_db()

# Define the route for the index page
@app.route('/')
def home():
    return render_template('home.html')

# Define the route for the verification page
@app.route('/google76aa80690a9a6bdd.html')
def verification():
    return render_template('google76aa80690a9a6bdd.html')

@app.route('/google76aa80690a9a6bdd')
def verification_v2():
    return render_template('google76aa80690a9a6bdd.html')

# Define the route for the API endpoints for annotation page
@app.route('/annotate', methods=['GET', 'POST'])
def load_annotation_page():
    # if the request is GET, simply render the annotation.html page
    if request.method == 'GET':
        return render_template('annotate.html')
    
    # if the request is POST, return the annotation.html page
    if request.method == 'POST':
        # get the participant information from the request
        participant_details = {'name'           : request.form['name'],
                               'age'            : request.form['age'],
                               'email'          : request.form['email'],
                               'gender'         : request.form['gender'],
                               'ethnicity'      : request.form['ethnicity'],
                               'background'     : request.form['background'],
                               'job'            : request.form['job'],
                               'physics'        : request.form.getlist('physics'),
                               'chemistry'      : request.form.getlist('chemistry'),
                               'biology'        : request.form.getlist('biology'),
                               'earth_sciences' : request.form.getlist('earth_sciences')}

        # generate the question bank for the participant
        question_bank = create_question_bank(global_args['hintGen_data_dir'])

        # initialize the dict to store the participant's demographics and the question bank for the participant
        participant_id, participant_responses = initialize_responses_dict(participant_details, question_bank, global_args) # This function auto-saves the participant's responses to the database
        print(participant_responses['question_0'].keys())
        
        # load the next page (survey or quiz depending on the hints asked)
        return load_next_page(participant_responses, participant_id, -1, global_args, message='')


# Define the route for the API endpoints for quiz page
@app.route('/quiz', methods=['GET', 'POST'])
def load_quiz_page():
    if request.method == 'GET':
        # Get participant_id and question_number from query parameters
        participant_id = request.args.get('participant_id')
        question_number = int(request.args.get('question_number', 0))
        if not participant_id:
            return "Missing participant_id", 400
        
        participant_responses = load_responses_dict(participant_id)
        # Load the quiz page for the given participant and question
        return load_same_page(participant_responses, participant_id, question_number, global_args)
    if request.method == 'POST':
        # get the participant id and question number from the request's hidden inputs
        participant_id = request.form['participant_id']
        question_number = int(request.form['question_number'])
        # load the participant's responses from the file
        participant_responses = load_responses_dict(participant_id)
        # key for the current question in the participant_responses
        question_key = 'question_' + str(question_number)

        # check if the "Want Hint?" button is clicked
        if request.form['submit'] == "Want Hint?": # Should not be accessible for the no-hint questions!

            # checl if max #hints have been reached
            if len(participant_responses[question_key]['hints']) == 4:
                return load_same_page(participant_responses, participant_id, question_number, global_args, message="No more hints available for this question.", good_message=False)

            # get the hint strategy for this question
            hint_strategy = participant_responses['strategy_order'][question_number]
            if hint_strategy == 'offline':
                # get the next offline hint for the question
                next_hint = get_offline_hint(participant_responses['Question Bank'][question_number]['question'], participant_responses[question_key]['hints'], global_args['hintGen_data_dir'])
            elif hint_strategy == 'online':
                # create the conversation_str based on the interaction logs of participant for this question
                conversation_str = "Learner's Interaction:\n"
                for action_entry in participant_responses[question_key]["action_log"]:
                    if action_entry['action'] == 'hint requested':
                        conversation_str += f"Hint: {action_entry['detail']}\n"
                    elif action_entry['action'] == 'wrong submission':
                        conversation_str += f"Attempted Answer: {action_entry['attempted_answer']}\n"
                if conversation_str.strip() == "Learner's Interaction:":
                    conversation_str += "No prior interactions.\n"

                # get the next online hint for the question
                next_hint = get_online_hint(question=participant_responses['Question Bank'][question_number]['question'],
                                            correct_answer=participant_responses['Question Bank'][question_number]['answer'], 
                                            conversation_str=conversation_str, 
                                            past_attempts=participant_responses[question_key]['attempted_answers'], 
                                            past_hints=participant_responses[question_key]['hints'])
            
            # update the participant's responses
            participant_responses = update_responses_dict(participant_responses, participant_id, question_key, add_hint=True, new_hint=next_hint)
            # return the quiz.html page with the same question and the next hint
            return load_same_page(participant_responses, participant_id, question_number, global_args, render_hint=next_hint)
        
        # check if the "Submit" button is clicked
        elif request.form['submit'] == "Submit":
            
            # if the attempted answer is correct, return the quiz.html page with the next question
            if check_answer(participant_responses['Question Bank'][question_number]['question'], request.form['answer'], participant_responses['Question Bank'][question_number]['answer']):

                # update the participant's responses
                participant_responses = update_responses_dict(participant_responses, participant_id, question_key, is_solved=True, attempted_answer=request.form['answer'])
                # load the next page (survey or quiz depending on the hints asked)
                return load_next_page(participant_responses, participant_id, question_number, global_args, check_for_survey=True, message="Correct! Well done. Here is the next question.", good_message=True)
            
            # if the attempted answer is wrong, check for the termination conditions and if it is met, move onto the next question.
            # otherwise return the quiz.html page with the same question and a message to try again
            else:
                # check if the participant has exhausted all attempts
                if participant_responses[question_key]["attempts"] >= global_args['total_attempts'] - 1:
                    # update the participant's responses
                    participant_responses = update_responses_dict(participant_responses, participant_id, question_key, attempted_answer=request.form['answer'], end_question=True, action="exhausted attempts")
                    # load the next page (survey or quiz depending on the hints asked)
                    return load_next_page(participant_responses, participant_id, question_number, global_args, check_for_survey=True, message=f'You have exhausted all the attempts for the previous question. The answer was "{participant_responses['Question Bank'][question_number]['answer']}". Here is the next question.', good_message=False)

                else:
                    # update the participant's responses to add the attempted answer
                    participant_responses = update_responses_dict(participant_responses, participant_id, question_key, wrong_attempt=True, attempted_answer=request.form['answer'])
                    # return the quiz.html page with the same question and a message to try again
                    return load_same_page(participant_responses, participant_id, question_number, global_args, message="Try Again! Incorrect Answer.", good_message=False)
        
        # check if the "Give up this question" button is clicked
        elif request.form['submit'] == "Give up this question":
            # update the participant's responses
            participant_responses = update_responses_dict(participant_responses, participant_id, question_key, attempted_answer=request.form['answer'], end_question=True, action="gave up the question")
            # load the next page (survey or quiz depending on the hints asked)
            return load_next_page(participant_responses, participant_id, question_number, global_args, check_for_survey=True, message=f'No worries, the answer to the last question was "{participant_responses['Question Bank'][question_number]['answer']}". Here is the next question.', good_message=False)


# Define the route for the API endpoints for hints survey page
@app.route('/survey', methods=['POST'])
def load_survey_page():
    if request.method == 'POST':
        # get the participant id from the request's hidden input
        participant_id = request.form['participant_id']
        # load the participant's responses from the file
        participant_responses = load_responses_dict(participant_id)
        # get the question number
        question_number = int(request.form['question_number'])
        # key for the current question in the participant_responses
        question_key = 'question_' + str(question_number)

        # update the participant's responses
        participant_responses[question_key]["action_log"].append({"action": "survey completed",
                                                                  "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

        # obtain the number of hints and the survey responses from the request
        number_of_hints = len(participant_responses[question_key]["hints"])
        survey_responses = [{'hint': participant_responses[question_key]['hints'][i], 
                             'response': request.form['hint' + str(i)],
                             'informitive': request.form['informativeness' + str(i)],
                             'leakage': request.form['leakage' + str(i)]
                             } for i in range(number_of_hints)]
        # update the participant's responses to include survey responses
        participant_responses = update_responses_dict(participant_responses, participant_id, question_key, survey_responses=survey_responses)
        
        return load_next_page(participant_responses, participant_id, question_number, global_args, check_for_survey=False, message="Thank you for your responses. Here is the next question.", good_message=True)


# Define the route for the API endpoints for custom hint generation page
@app.route('/custom', methods=['GET', 'POST'])
def run_custom_example():
    # if the request is POST, generate hints and return the custom_hints.html page
    if request.method == 'POST':

        # check if the "Submit" button is clicked
        if request.form['submit'] == "Submit":
            # get the question, answer, and context from the request
            question = request.form['question']
            answer = request.form['answer']
            context = request.form['context']

            # check if answer or context are empty
            if not answer:
                answer = None
            if not context:
                context = None

            print("Question:", question)
            print("Answer:", answer)
            print("Context:", context)

            # generate hints for the given question, answer, and context
            generated_hints = generate_custom_hints(question, answer, context)
            # convert the hints to HTML format
            generated_hints_html = "<h3> All the generated hints: </h3>\n"
            generated_hints_html += "<ol>" + "".join(["<li>" + hint + "</li>" for hint in generated_hints]) + "</ol>"

            # iterate over selection strategies and select appropriate hints
            selected_hints = "<h3> Selected Hints: </h3>\n"
            for strategy in global_args['hint_selection_strategies']:
                selected_hint = global_args['hint_selection_strategies'][strategy](generated_hints)
                selected_hint = "<b>Selected Hint (" + strategy + "):</b> " + selected_hint + "<br>"
                selected_hints += selected_hint
            
            return render_template('custom.html', 
                                question=question, 
                                answer=answer, 
                                context=context, 
                                generated_hints=generated_hints_html, 
                                selected_hints=selected_hints)
        
        # check if the "Go Back" button is clicked
        elif request.form['submit'] == "Go Back":
            return render_template('home.html')
    
    # if the request is GET, return the custom.html page
    if request.method == 'GET':
        return render_template('custom.html')


@app.route('/past_hints', methods=['POST'])
def view_past_hints():
    # this means that the user has clicked on the "View Past Hints" display
    # denoting that the user is making use of other hints to answer the question
    # get the participant id from the request's hidden input
    data = json.loads(request.data)
    curr_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    participant_id = data['participant_id']
    question_number = int(data['question_number'])
    # update the action log for the participant
    participant_responses = load_responses_dict(participant_id)
    question_key = 'question_' + str(question_number)
    participant_responses[question_key]["action_log"].append({"action": "viewed past hints",
                                                              "timestamp": curr_timestamp})
    # save the participant's responses to the database
    participant_responses = update_responses_dict(participant_responses, participant_id, question_key)
    # return the quiz.html page with the same question and a message to try again
    return load_same_page(participant_responses, participant_id, question_number, global_args, message="NOTHING", good_message=True)


# Define the route for the API endpoints for remarks page (to render the thank you page)
@app.route('/remarks', methods=['POST'])
def return_thank_you():
    # AJ: resolve the ranking parsing (once the questions are finalized.)
    remarks = {"q1": request.form['q1'],
               "q2": request.form['q2'],
               "q3": request.form['q3'],
               "q4": request.form['q4'],}
    
    participant_id = request.form['participant_id']
    # save the remarks to the database
    participant_responses = load_responses_dict(participant_id)
    participant_responses['remarks'] = remarks
    # save the participant's responses to the database
    save_response_dict(participant_id, participant_responses)
    # return the thank you page
    return load_thank_you_page(participant_responses, participant_id)

# Define the route for the API endpoints for remarks page (to render the thank you page)
@app.route('/sectionsurvey', methods=['POST'])
def load_section_survey():
    participant_id = request.form['participant_id']
    question_number = int(request.form['question_number']) + 1
    assert question_number in [10, 20, 30], "Question number should be one of the section ends (10, 20, 30), it is " + str(question_number)
    # map the question number to the section number
    section_map = {10: 1, 20: 2, 30: 3}
    section_number = section_map.get(question_number, 3)  # default to section

    if section_number == 1: # no hints section
        responses = {"q1": request.form['q1']}
    else: # hints section
        responses = {"q1": request.form['q1'],
                     "q2": request.form['q2'],
                     "q3": request.form['q3'],
                     "q4": request.form['q4'],}
    
    # save the responses to the database
    participant_responses = load_responses_dict(participant_id)
    participant_responses[f'section_survey_{section_number}'] = responses

    # update the break end time
    participant_responses = update_responses_dict(participant_responses, participant_id, 'question_' + str(question_number), end_break=True)

    # save the participant's responses to the database
    save_response_dict(participant_id, participant_responses)
    if section_number < 3:
        # return the next quiz page (with next question number)
        return load_next_page(participant_responses, participant_id, question_number-1, global_args, check_for_survey=False, message="Thank you for your responses. Here is the next question.", good_message=True)
    else:
        section_info_revealing_str = ""
        if participant_responses['strategy_order'][11] == 'offline': # section 2 is offline, section 3 is online
            section_info_revealing_str = "Hints presented in Section 2 were a pre-determined set of suggestions. <br>Hints presented in Section 3 were designed to be adaptive to your previous attempt for the question."
        else:
            section_info_revealing_str = "Hints presented in Section 3 were a pre-determined set of suggestions. <br>Hints presented in Section 2 were designed to be adaptive to your previous attempt for the question."
        # return the remarks page (final survey page)
        return render_template('remarks.html', 
                               participant_id=participant_id, 
                               question_number=question_number, 
                               global_args=global_args,
                               section_info_revealing_str=section_info_revealing_str,
                               qa_pairs_html_section_1=get_qa_pairs_html(participant_responses, section_no=1),
                               qa_pairs_html_section_2=get_qa_pairs_html(participant_responses, section_no=2),
                               qa_pairs_html_section_3=get_qa_pairs_html(participant_responses, section_no=3))


# Define the route for the API endpoints for the plot analysis
@app.route('/plots', methods=['GET', 'POST'])
def get_plots():
    # # obtain the data from Heroku's PygreSQL database
    # data = fetch_heroku_data()
    # Obtain the data from the study
    data = json.load(open("../data/human_eval/scientific_hint_generation_study_responses.json", 'r'))

    # obtain the list of questions
    questions_html = get_questions_html()

    # first generate all the plots (unless they are already generated)
    # Also get the number of participants
    num_participants = generate_all_plots(data)
    print("Number of participants:", num_participants)

    if request.method == 'GET':
        return render_template('plots.html', 
                               plot_jsons='',
                               questions_html=questions_html,
                               num_participants=num_participants)

    if request.method == 'POST':
        # check if the "Submit" button is clicked
        if request.form['submit'] == "Submit":
            print("Plotting....", [(k, request.form[k]) for k in request.form.keys()])

            # obtain the plot based on the request
            plot_jsons = obtain_plot(data, request.form)

            # print(plot_jsons) # for debugging
            
            return render_template('plots.html', 
                                plot_jsons=plot_jsons,
                                questions_html=questions_html,
                                num_participants=num_participants)

        # check if the "Go Back" button is clicked
        elif request.form['submit'] == "Go Back":
            return render_template('home.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)