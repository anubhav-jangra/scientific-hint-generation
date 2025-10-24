import os
import json
import psycopg2
import plotly.io as pio

from Plots.utils import get_participant_details_new, save_filtered_data, get_info_score
from Plots.aggregate_utils import agg_plot_1, agg_plot_2, agg_plot_3, agg_plot_4_new
from Plots.individual_utils import ind_plot_1, ind_plot_2_v2, ind_plot_3, ind_plot_4, ind_plot_5_v2, ind_plot_6
from Plots.scatter_utils import obtain_scatter_plot

def get_filtered_data(data):
    # filtered_data = json.load(open("../../data/human_eval/scientific_hint_generation_study_responses.json"), 'r')
    # sort the filtered data by begin_time
    filtered_data = {}
    for idx, response in enumerate(data):
        filtered_data[f'P-{idx+1}'] = response
    final_data = {}
    filtered_data = dict(sorted(filtered_data.items(), key=lambda item: item[1]['begin_time'].replace('Z', '+00:00')))
    for idx, (participant_id, participant_data) in enumerate(filtered_data.items()):
        final_data[f'P-{idx+1}'] = participant_data

    return final_data

def obtain_plot(data, plot_details):
    plots_save_dir = "Plots/plots"

    if plot_details['plot_type'] == 'individual':

        if plot_details['participant_id'] is not None:
            # generate an individual plot for a specific user with this participant_id
            # obtain the individual plots
            ind_plots = json.load(open(os.path.join(plots_save_dir, "individual_plots.json")))
            plot_jsons = []
            for plot_name, plot_data in ind_plots[plot_details['participant_id']].items():
                _fig = pio.from_json(plot_data)
                plot_jsons.append(pio.to_json(_fig))
            return plot_jsons
        else:
            raise ValueError("Please provide either an email or a participant_id to generate an individual plot.")
    
    elif plot_details['plot_type'] == 'aggregate':
        # obtain an aggregate plot
        aggregate_plots = json.load(open(os.path.join(plots_save_dir, "aggregate_plots.json")))
        plot_jsons = []
        for plot_name, plot_data in aggregate_plots.items():
            _fig = pio.from_json(plot_data)
            plot_jsons.append(pio.to_json(_fig))
        return plot_jsons

    elif plot_details['plot_type'] == 'informativeness':
        # get the question number
        _question = plot_details['question_str']

        # obtain the informativeness scatter plots
        scatter_plots = json.load(open(os.path.join(plots_save_dir, "scatter_plots.json")))
        plot_jsons = []
        for embed_model in ["nvidia/NV-Embed-v2", "sentence-transformers/stsb-roberta-large",
        "sentence-transformers/all-MiniLM-L6-v2", "Alibaba-NLP/gte-Qwen2-7B-instruct"]:
            _fig = pio.from_json(scatter_plots[embed_model.split('/')[-1]][_question])
            plot_jsons.append(pio.to_json(_fig))
        return plot_jsons
        
    else:
        raise ValueError("Invalid plot type. Please choose between 'individual' and 'aggregate'.")


def generate_all_plots(data):
    """
    A function to genreate all possible plots and save their corresponding renderable information as a JSON file.
    The files are stored in 'Plots/plots_old' directory.
    
    Args:
        data (dict) : The response data obtained from the HintGenUI to be plotted.
                      This is the raw data obtained from the interaction database in Heroku's PostgreSQL backend.
    
    Returns:
        num_participants: The total number of participants in the data after filtering out the invalid participants and test participants.
    """
    plots_save_dir = "Plots/plots"
    data_save_dir = "Plots/responses"

    # ensure that the save directories exists
    if not os.path.exists(plots_save_dir):
        os.makedirs(plots_save_dir)
    if not os.path.exists(data_save_dir):
        os.makedirs(data_save_dir)
    
    # filter out the data to remove the invalid participants and test participants
    filtered_data = get_filtered_data(data) # save_filtered_data(data, out_file_name=None) # "Plots/responses/filtered_data.json")
    # use the uncommented line when the data is actual data from pysql, and not a loaded version of finalized data

    # obtain the participant details for each participant
    plot_data = {participant_id: get_participant_details_new(participant_data) for participant_id, participant_data in filtered_data.items()}

    # Before generating the plots
    #  check if the plots have been already generated, in which case skip the generation
    if if_new_data(data):
        return len(plot_data)

    # generate the individual plots
    individual_plots = {}

    for participant_id, participant_data in plot_data.items():

        ind_plt1 = ind_plot_1(participant_data)
        ind_plt2 = ind_plot_2_v2(participant_data)
        ind_plt3 = ind_plot_3(participant_data)
        ind_plt4 = ind_plot_4(participant_data)
        ind_plt5 = ind_plot_5_v2(participant_data)
        ind_plt6 = ind_plot_6(participant_data)

        individual_plots[participant_id] = {'ind_plot_1': ind_plt1, 
                                            'ind_plot_2': ind_plt2,
                                            'ind_plot_3': ind_plt3,
                                            'ind_plot_4': ind_plt4,
                                            'ind_plot_5': ind_plt5,
                                            'ind_plot_6': ind_plt6
        }
    
    # save the individual plots to a file
    with open(os.path.join(plots_save_dir, "individual_plots.json"), 'w') as f:
        json.dump(individual_plots, f, indent=4)

    # generate the aggregate plots and obtain their json strings
    aggregate_plots = {}

    agg_plt1 = agg_plot_1(plot_data)
    agg_plt2 = agg_plot_2(plot_data)
    agg_plt3 = agg_plot_3(plot_data)
    agg_plt4 = agg_plot_4_new(plot_data) # different baselines in new evaluation setting

    aggregate_plots['agg_plot_1'] = agg_plt1
    aggregate_plots['agg_plot_2'] = agg_plt2
    aggregate_plots['agg_plot_3'] = agg_plt3
    aggregate_plots['agg_plot_4'] = agg_plt4

    # save the aggregate plots to a file
    with open(os.path.join(plots_save_dir, "aggregate_plots.json"), 'w') as f:
        json.dump(aggregate_plots, f, indent=4)

    
    # load the quiz data
    quiz_data = json.load(open('hintGen/quiz_data/quiz_old.json', 'r'))

    scatter_plots = {}
    # generate the informaitveness scatter plots
    for embed_model in ["nvidia/NV-Embed-v2", "sentence-transformers/stsb-roberta-large",
        "sentence-transformers/all-MiniLM-L6-v2", "Alibaba-NLP/gte-Qwen2-7B-instruct"]:
        scatter_plots[embed_model.split('/')[-1]] = {}
        # load the question-hint similarity data
        quiz_similarity_data = json.load(open(f'hintGen/quiz_data/quiz_similarity_{embed_model.split('/')[-1]}.json', 'r'))
        for inst_idx, inst in enumerate(quiz_similarity_data):
            question = inst['question']
            # obtain the informativeness scatter plot for this question
            inst['informativeness_score'] = get_info_score(inst['question_similarity'], inst['answer_similarity'], inst['answer'], _threshold=0.8)
            # augment the raw hint responses from the quiz_data
            inst['raw_hints'] = quiz_data[inst_idx]['hints']
            # add the model name into the instance
            inst['embed_model'] = embed_model.split('/')[-1]
            # collect the informativeness score for this question
            scatter_plots[embed_model.split('/')[-1]][question] = obtain_scatter_plot(inst)

    # save the scatter plots to a file
    with open(os.path.join(plots_save_dir, "scatter_plots.json"), 'w') as f:
        json.dump(scatter_plots, f, indent=4)

    # return the number of participants for the main function
    # (This is used to display the number of participants in the UI)
    return len(plot_data)

def if_new_data(data):
    """
    A function to check if there is new data in the database.
    If there is new data, then return True, otherwise return False.

    Args:
        data (dict) : The response data obtained from the HintGenUI to be plotted.
                      This is the raw data obtained from the interaction database in Heroku's PostgreSQL backend.

    Returns:
        bool : True if there is new data, False otherwise.
    """
    return False