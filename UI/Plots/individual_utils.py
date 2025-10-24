import plotly.io as pio
import plotly.subplots as sp
import plotly.graph_objs as go

from Plots.utils import get_time_difference

# Define the color maps for all the plots
def obtain_plot_maps():
    # Define the color maps for all the subplots
    domain_color_mapping = {'physics': 'Orchid', 'chemistry': 'Magenta', 'biology': 'RebeccaPurple', 'earth science': 'DarkViolet'} # , 'miscellaneous': 'Lavender'}
    # define the color mapping for the actions
    action_color_map = {'started question': 'black',
                        'hint requested': 'blue',
                        'wrong submission': 'red',
                        'gave up the question': 'orange',
                        'viewed past hints': 'purple',
                        'survey completed': 'green',
                        'correct submission': 'gold',
                        'exhausted attempts': 'brown'}
    strategy_color_mapping = {0: 'Bisque', 1: 'SandyBrown', 2: 'Chocolate', 3: 'Brown'}
    strategy_color_mapping_new = {'no-hint': 'SandyBrown', 'offline': 'Chocolate', 'online': 'Brown'}

    return domain_color_mapping, action_color_map, strategy_color_mapping, strategy_color_mapping_new

def ind_plot_1(_data):
    """
    Plot the first individual analysis plot of the data. 
    This plot specifically plots the individual's performance in the quiz across subjects.
    
    Args:
        _data (dict) : The plot data obtained from the utils.get_participant_details function.
    
    Returns:
        JSON string : The JSON string containing the plot data.
    """

    # get the color maps for the plot
    domain_color_mapping, _, _, _ = obtain_plot_maps()

    # initialize a plotly figure to plot the data
    _fig = go.Figure()
    # update the layout of the figure
    _fig.update_layout(title={
                            'text': f"Total Hints asked (subjects)",
                            'y':0.98,
                            'x':0.45,
                        },
    )

    for _domain in domain_color_mapping.keys():
        # for i in range(_data['total_questions']):
        #     print(_data['question_domain_mapping'])
        #     print(_data['questions'])
        #     if _data['question_domain_mapping'][_data['questions'][i]] == _domain:
        #         print(_data['Question Bank'][i]['question'])
        _fig.add_trace(go.Bar(
            x=[i for i in range(_data['total_questions']) if _data['question_domain_mapping'][_data['questions'][i]] == _domain],
            y=[len(_data['hints'][i]) for i in range(_data['total_questions']) if _data['question_domain_mapping'][_data['questions'][i]] == _domain],
            hoverinfo='text',
            hovertext=[f"Question: {_data['questions'][q_id]}<br>" + 
                    f"Answer: {_data['answers'][q_id]}<br>" + 
                    f"Attempted answers: " + ", ".join(_data['attempted_answers'][q_id]) + "<br>" +
                    f"Subject: {_domain}<br>" +
                    "<br>".join([f"Hint {idx}: {hint}" for idx, hint in enumerate(hints)]) for q_id, hints in enumerate(_data['hints']) if _data['question_domain_mapping'][_data['questions'][q_id]] == _domain],
            textposition='auto',
            marker_color=domain_color_mapping[_domain],
            marker_line=dict(
                width=[2] * _data['total_questions'],
                color='black',
            ),
            name=_domain,
        ))
    
    # Scatter plot with markers to denote the successful questions
    _fig.add_trace(go.Scatter(
        x=[i for i, condition in enumerate(_data['correctly_answered']) if condition],  # Change the condition as needed
        y=[len(hints) + 0.2 for i, (condition, hints) in enumerate(zip(_data['correctly_answered'], _data['hints'])) if condition],  # Change the condition as needed
        mode='markers',
        marker=dict(
            size=15,
            color='gold',
            symbol='star',
            line=dict(
                width=2,
                color='black',
            ),
        ),
        hoverinfo='text',
        hovertext=[f"Question: {_data['questions'][q_id]}<br>" + 
                    f"Answer: {_data['answers'][q_id]}<br>" + 
                    f"Attempted answers: " + ", ".join(_data['attempted_answers'][q_id]) + "<br>" +
                    f"Subject: {_data['question_domain_mapping'][_data['questions'][q_id]]}<br>" +
                    "<br>".join([f"Hint {idx}: {hint}" for idx, hint in enumerate(hints)])
                      for q_id, (condition, hints) in enumerate(zip(_data['correctly_answered'], _data['hints'])) if condition
                    ],
        name="P1-Correct",
    ))

    # Scatter plot with markers to denote the skipped questions
    _fig.add_trace(go.Scatter(
        x=[i for i, condition in enumerate(_data['skipped_question']) if condition],  # Change the condition as needed
        y=[len(hints) + 0.2 for i, (condition, hints) in enumerate(zip(_data['skipped_question'], _data['hints'])) if condition],  # Change the condition as needed
        mode='markers',
        marker=dict(
            size=15,
            color='Salmon',
            symbol='bowtie',
            line=dict(
                width=2,
                color='black',
            ),
        ),
        hoverinfo='text',
        hovertext=[f"Question: {_data['questions'][q_id]}<br>" + 
                    f"Answer: {_data['answers'][q_id]}<br>" + 
                    f"Attempted answers: " + ", ".join(_data['attempted_answers'][q_id]) + "<br>" +
                    f"Subject: {_data['question_domain_mapping'][_data['questions'][q_id]]}<br>" +
                    "<br>".join([f"Hint {idx}: {hint}" for idx, hint in enumerate(hints)]) 
                    for q_id, (condition, hints) in enumerate(zip(_data['skipped_question'], _data['hints'])) if condition],
        name="Skipped",
    ))

    # Scatter plot with markers to denote the exhausted questions
    _fig.add_trace(go.Scatter(
        x=[i for i, condition in enumerate(_data['exhausted_attemps']) if condition],  # Change the condition as needed
        y=[len(hints) + 0.2 for i, (condition, hints) in enumerate(zip(_data['exhausted_attemps'], _data['hints'])) if condition],  # Change the condition as needed
        mode='markers',
        marker=dict(
            size=15,
            color='Crimson',
            symbol='x',
            line=dict(
                width=2,
                color='black',
            ),
        ),
        hoverinfo='text',
        hovertext=[f"Question: {_data['questions'][q_id]}<br>" + 
                    f"Answer: {_data['answers'][q_id]}<br>" + 
                    f"Attempted answers: " + ", ".join(_data['attempted_answers'][q_id]) + "<br>" +
                    f"Subject: {_data['question_domain_mapping'][_data['questions'][q_id]]}<br>" +
                    "<br>".join([f"Hint {idx}: {hint}" for idx, hint in enumerate(hints)]) 
                    for q_id, (condition, hints) in enumerate(zip(_data['exhausted_attemps'], _data['hints'])) if condition],
        name="Exhausted",
    ))

    # change the background color
    _fig.update_layout(
        plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
    )

    # convert the plot to JSON format
    plot_json = pio.to_json(_fig)

    return plot_json

def ind_plot_2(_data):
    """
    Plot the second individual analysis plot of the data. 
    This plot specifically plots the individual's performance in the quiz across strategies.
    
    Args:
        _data (dict) : The plot data obtained from the utils.get_participant_details function.
    
    Returns:
        JSON string : The JSON string containing the plot data.
    """

    # get the color maps for the plot
    _, _, strategy_color_mapping, _ = obtain_plot_maps()

    # initialize a plotly figure to plot the data
    _fig = go.Figure()
    # update the layout of the figure
    _fig.update_layout(title={
                            'text': f"Total Hints asked (hint selection strategy)",
                            'y':0.98,
                            'x':0.45,
                        },
    )

    strategy_name_mapping = {0: 'random', 1: 'longest', 2: 'kmedoid', 3: 'dp'}
    for strategy in strategy_color_mapping.keys():
        _fig.add_trace(go.Bar(
            x=[i for i in range(_data['total_questions']) if _data['hint_strategies'][i] == strategy_name_mapping[strategy]],
            y=[len(_data['hints'][i]) for i in range(_data['total_questions']) if _data['hint_strategies'][i] == strategy_name_mapping[strategy]],
            hoverinfo='text',
            hovertext=[f"Question: {_data['questions'][q_id]}<br>" + 
                    f"Answer: {_data['answers'][q_id]}<br>" + 
                    f"Hint strategy: {strategy_name_mapping[strategy]}<br>" +
                    f"Attempted answers: " + ", ".join(_data['attempted_answers'][q_id]) + "<br>" +
                    "<br>".join([f"Hint {idx}: {hint}" for idx, hint in enumerate(hints)]) for q_id, hints in enumerate(_data['hints']) if _data['hint_strategies'][q_id] == strategy_name_mapping[strategy]],
            textposition='auto',
            marker_color=strategy_color_mapping[strategy],
            marker_line=dict(
                width=[2] * _data['total_questions'], 
                color='black',
            ),
            name=strategy_name_mapping[strategy],
        ))

    # Scatter plot with markers to denote the successful questions
    _fig.add_trace(go.Scatter(
        x=[i for i, condition in enumerate(_data['correctly_answered']) if condition],  # Change the condition as needed
        y=[len(hints) + 0.2 for i, (condition, hints) in enumerate(zip(_data['correctly_answered'], _data['hints'])) if condition],  # Change the condition as needed
        mode='markers',
        marker=dict(
            size=15,
            color='gold',
            symbol='star',
            line=dict(
                width=2,
                color='black',
            ),
        ),
        hoverinfo='text',
        hovertext=[f"Question: {_data['questions'][q_id]}<br>" + 
                    f"Answer: {_data['answers'][q_id]}<br>" + 
                    f"Hint strategy: {strategy_name_mapping[strategy]}<br>" +
                    f"Attempted answers: " + ", ".join(_data['attempted_answers'][q_id]) + "<br>" +
                    "<br>".join([f"Hint {idx}: {hint}" for idx, hint in enumerate(hints)]) 
                    for q_id, (condition, hints) in enumerate(zip(_data['correctly_answered'], _data['hints'])) if condition],
        name="Correct",
    ))

    # Scatter plot with markers to denote the skipped questions
    _fig.add_trace(go.Scatter(
        x=[i for i, condition in enumerate(_data['skipped_question']) if condition],  # Change the condition as needed
        y=[len(hints) + 0.2 for i, (condition, hints) in enumerate(zip(_data['skipped_question'], _data['hints'])) if condition],  # Change the condition as needed
        mode='markers',
        marker=dict(
            size=15,
            color='Salmon',
            symbol='bowtie',
            line=dict(
                width=2,
                color='black',
            ),
        ),
        hoverinfo='text',
        hovertext=[f"Question: {_data['questions'][q_id]}<br>" + 
                    f"Answer: {_data['answers'][q_id]}<br>" + 
                    f"Subject: {_data['question_domain_mapping'][_data['questions'][q_id]]}<br>" +
                    "<br>".join([f"Hint {idx}: {hint}" for idx, hint in enumerate(hints)]) 
                    for q_id, (condition, hints) in enumerate(zip(_data['skipped_question'], _data['hints'])) if condition],
        name="Skipped",
    ))

    # Scatter plot with markers to denote the exhausted questions
    _fig.add_trace(go.Scatter(
        x=[i for i, condition in enumerate(_data['exhausted_attemps']) if condition],  # Change the condition as needed
        y=[len(hints) + 0.2 for i, (condition, hints) in enumerate(zip(_data['exhausted_attemps'], _data['hints'])) if condition],  # Change the condition as needed
        mode='markers',
        marker=dict(
            size=15,
            color='Crimson',
            symbol='x',
            line=dict(
                width=2,
                color='black',
            ),
        ),
        hoverinfo='text',
        hovertext=[f"Question: {_data['questions'][q_id]}<br>" + 
                    f"Answer: {_data['answers'][q_id]}<br>" + 
                    f"Attempted answers: " + ", ".join(_data['attempted_answers'][q_id]) + "<br>" +
                    f"Subject: {_data['question_domain_mapping'][_data['questions'][q_id]]}<br>" +
                    "<br>".join([f"Hint {idx}: {hint}" for idx, hint in enumerate(hints)]) 
                    for q_id, (condition, hints) in enumerate(zip(_data['exhausted_attemps'], _data['hints'])) if condition],
        name="Exhausted",
    ))

    # Add axis labels
    _fig.update_xaxes(title_text="Question Number")
    _fig.update_yaxes(title_text="Total hints asked")

    # change the background color
    _fig.update_layout(
        plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
    )

    # convert the plot to JSON format
    plot_json = pio.to_json(_fig)

    return plot_json

def ind_plot_2_v2(_data):
    """
    Plot the second individual analysis plot of the data. 
    This plot specifically plots the individual's performance in the quiz across strategies.
    
    Args:
        _data (dict) : The plot data obtained from the utils.get_participant_details function.
    
    Returns:
        JSON string : The JSON string containing the plot data.
    """

    # get the color maps for the plot
    _, _, _, strategy_color_mapping = obtain_plot_maps()

    # initialize a plotly figure to plot the data
    _fig = go.Figure()
    # update the layout of the figure
    _fig.update_layout(title={
                            'text': f"Total Hints asked (hint selection strategy)",
                            'y':0.98,
                            'x':0.45,
                        },
    )

    for strategy in strategy_color_mapping.keys():
        _fig.add_trace(go.Bar(
            x=[i for i in range(_data['total_questions']) if _data['hint_strategies'][i] == strategy],
            y=[len(_data['hints'][i]) for i in range(_data['total_questions']) if _data['hint_strategies'][i] == strategy],
            hoverinfo='text',
            hovertext=[f"Question: {_data['questions'][q_id]}<br>" + 
                    f"Answer: {_data['answers'][q_id]}<br>" + 
                    f"Hint strategy: {strategy}<br>" +
                    f"Attempted answers: " + ", ".join(_data['attempted_answers'][q_id]) + "<br>" +
                    "<br>".join([f"Hint {idx}: {hint}" for idx, hint in enumerate(hints)]) for q_id, hints in enumerate(_data['hints']) if _data['hint_strategies'][q_id] == strategy],
            textposition='auto',
            marker_color=strategy_color_mapping[strategy],
            marker_line=dict(
                width=[2] * _data['total_questions'], 
                color='black',
            ),
            name=strategy,
        ))

    # Scatter plot with markers to denote the successful questions
    _fig.add_trace(go.Scatter(
        x=[i for i, condition in enumerate(_data['correctly_answered']) if condition],  # Change the condition as needed
        y=[len(hints) + 0.2 for i, (condition, hints) in enumerate(zip(_data['correctly_answered'], _data['hints'])) if condition],  # Change the condition as needed
        mode='markers',
        marker=dict(
            size=15,
            color='gold',
            symbol='star',
            line=dict(
                width=2,
                color='black',
            ),
        ),
        hoverinfo='text',
        hovertext=[f"Question: {_data['questions'][q_id]}<br>" + 
                    f"Answer: {_data['answers'][q_id]}<br>" + 
                    f"Hint strategy: {strategy}<br>" +
                    f"Attempted answers: " + ", ".join(_data['attempted_answers'][q_id]) + "<br>" +
                    "<br>".join([f"Hint {idx}: {hint}" for idx, hint in enumerate(hints)]) 
                    for q_id, (condition, hints) in enumerate(zip(_data['correctly_answered'], _data['hints'])) if condition],
        name="Correct",
    ))

    # Scatter plot with markers to denote the skipped questions
    _fig.add_trace(go.Scatter(
        x=[i for i, condition in enumerate(_data['skipped_question']) if condition],  # Change the condition as needed
        y=[len(hints) + 0.2 for i, (condition, hints) in enumerate(zip(_data['skipped_question'], _data['hints'])) if condition],  # Change the condition as needed
        mode='markers',
        marker=dict(
            size=15,
            color='Salmon',
            symbol='bowtie',
            line=dict(
                width=2,
                color='black',
            ),
        ),
        hoverinfo='text',
        hovertext=[f"Question: {_data['questions'][q_id]}<br>" + 
                    f"Answer: {_data['answers'][q_id]}<br>" + 
                    f"Subject: {_data['question_domain_mapping'][_data['questions'][q_id]]}<br>" +
                    "<br>".join([f"Hint {idx}: {hint}" for idx, hint in enumerate(hints)]) 
                    for q_id, (condition, hints) in enumerate(zip(_data['skipped_question'], _data['hints'])) if condition],
        name="Skipped",
    ))

    # Scatter plot with markers to denote the exhausted questions
    _fig.add_trace(go.Scatter(
        x=[i for i, condition in enumerate(_data['exhausted_attemps']) if condition],  # Change the condition as needed
        y=[len(hints) + 0.2 for i, (condition, hints) in enumerate(zip(_data['exhausted_attemps'], _data['hints'])) if condition],  # Change the condition as needed
        mode='markers',
        marker=dict(
            size=15,
            color='Crimson',
            symbol='x',
            line=dict(
                width=2,
                color='black',
            ),
        ),
        hoverinfo='text',
        hovertext=[f"Question: {_data['questions'][q_id]}<br>" + 
                    f"Answer: {_data['answers'][q_id]}<br>" + 
                    f"Attempted answers: " + ", ".join(_data['attempted_answers'][q_id]) + "<br>" +
                    f"Subject: {_data['question_domain_mapping'][_data['questions'][q_id]]}<br>" +
                    "<br>".join([f"Hint {idx}: {hint}" for idx, hint in enumerate(hints)]) 
                    for q_id, (condition, hints) in enumerate(zip(_data['exhausted_attemps'], _data['hints'])) if condition],
        name="Exhausted",
    ))

    # Add axis labels
    _fig.update_xaxes(title_text="Question Number")
    _fig.update_yaxes(title_text="Total hints asked")

    # change the background color
    _fig.update_layout(
        plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
    )

    # convert the plot to JSON format
    plot_json = pio.to_json(_fig)

    return plot_json

def ind_plot_3(_data):
    """
    Plot the third individual analysis plot of the data. 
    This plot specifically plots the subject-wise performance.
    
    Args:
        _data (dict) : The plot data obtained from the utils.get_participant_details function.
    
    Returns:
        JSON string : The JSON string containing the plot data.
    """

    # get the color maps for the plot
    domain_color_mapping, _, _, _ = obtain_plot_maps()

    # initialize a plotly figure to plot the data
    _fig = go.Figure()
    # update the layout of the figure
    _fig.update_layout(title={
                            'text': f"Subject-wise performance",
                            'y':0.98,
                            'x':0.45,
                        },
    )

    # plot the domain-wise success of the participant
    domain_questions, domain_correctly_answered, domain_total_hints_asked, domain_total_time_spent = {}, {}, {}, {}
    question_order_dict = {question: idx for idx, question in enumerate(_data['questions'])} # needed for _data['question_domain_mapping']
    for _domain in domain_color_mapping.keys():
        domain_questions[_domain]          = sum([1 for question, domain in _data['question_domain_mapping'].items() if domain == _domain])
        domain_correctly_answered[_domain] = sum([1 for question, domain in _data['question_domain_mapping'].items() if domain == _domain and _data['correctly_answered'][question_order_dict[question]] == 1])
        domain_total_hints_asked[_domain]  = sum([len(_data['hints'][question_order_dict[question]]) for question, domain in _data['question_domain_mapping'].items() if domain == _domain])
        domain_total_time_spent[_domain]   = sum([_data['total_time_spent'][question_order_dict[question]] for question, domain in _data['question_domain_mapping'].items() if domain == _domain]) / 60 # convert to minutes
    

    def get_domain_plot_value(_domain, metric):
        if metric == 'Subject confidence (self reported)':
            _domain = _domain.replace("earth science", "earth_sciences")
            return _data['subject_confidence'][_domain]
        elif metric == 'Total Questions':
            return domain_questions[_domain]
        elif metric == 'Correctly Answered':
            return domain_correctly_answered[_domain]
        elif metric == 'Hints Asked (Across all questions)':
            return domain_total_hints_asked[_domain]
        elif metric == 'Total Time Spent':
            return domain_total_time_spent[_domain]
        else:
            return 0

    # Create a bar graph grouping each metric for each domain
    domain_metrics = ['Subject confidence (self reported)', 'Total Questions', 'Correctly Answered', 'Hints Asked (Across all questions)', 'Total Time Spent']
    # Create a bar for each domain for each metric
    for idx, metric in enumerate(domain_metrics):
        for _idx, _domain in enumerate(domain_color_mapping.keys()):
            _fig.add_trace(go.Bar(
                x=[metric],  # Set the x value to the metric name
                y=[get_domain_plot_value(_domain, metric)],  # Set the y value based on the metric
                name=_domain,  # Set the trace name to the domain name
                marker_color=domain_color_mapping[_domain],  # Set the bar color based on the domain
                offsetgroup=_idx,  # Use different offsetgroup for each domain
                hoverinfo='text',  # Set the hover info to text
                hovertext=f'Domain: {_domain}<br>Metric: {metric}<br>Value: {round(get_domain_plot_value(_domain, metric), 3)}',  # Set the hover text
                showlegend=True if idx == 0 else False,  # Show legend only for the first metric
            ), )

    # Set the bar mode to 'group'
    _fig.update_layout(
        barmode='group',
        plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
    )
    # Add axis labels
    _fig.update_xaxes(title_text="Performance measures")
    _fig.update_yaxes(title_text="Metric Value")

    # change the background color
    _fig.update_layout(
        plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
    )

    # convert the plot to JSON format
    plot_json = pio.to_json(_fig)

    return plot_json

def ind_plot_4(_data):
    """
    Plot the fourth individual analysis plot of the data. 
    This plot specifically plots the hint reported scores (subject wise).
    
    Args:
        _data (dict) : The plot data obtained from the utils.get_participant_details function.
    
    Returns:
        JSON string : The JSON string containing the plot data.
    """

    # get the color maps for the plot
    domain_color_mapping, _, _, _ = obtain_plot_maps()

    # initialize a plotly figure to plot the data
    _fig = go.Figure()
    # update the layout of the figure
    _fig.update_layout(title={
                            'text': f"Hint Satisfaction ratings (across subjects)",
                            'y':0.98,
                            'x':0.45,
                        },
    )

    score_value_mapping = {'1': "Strongly Dissatisfied", '2': "Dissatisfied", '3': "Neutral", '4': "Satisfied", '5': "Strongly Satisfied"}
    domain_score_mapping = {domain: {_k: 0 for _k in score_value_mapping.keys()} for domain in domain_color_mapping.keys()}
    for domain in domain_color_mapping.keys():
        for q_no, question_responses in enumerate(_data['survey_responses']):
            if _data['question_domain_mapping'][_data['questions'][q_no]] == domain:
                for _idx, response in enumerate(_data['survey_responses'][q_no]):
                    domain_score_mapping[domain][response['response']] += 1

    # Create a bar for each domain for each score value
    for idx, score_value in enumerate(score_value_mapping.keys()):
        for _idx, _domain in enumerate(domain_color_mapping.keys()):
            _fig.add_trace(go.Bar(
                x=[score_value_mapping[score_value]],  # Set the x value to the metric name
                y=[domain_score_mapping[_domain][score_value]],  # Set the y value based on the metric
                name=_domain,  # Set the trace name to the domain name
                marker_color=domain_color_mapping[_domain],  # Set the bar color based on the domain
                offsetgroup=_idx,  # Use different offsetgroup for each domain
                hoverinfo='text',  # Set the hover info to text
                hovertext=f'Domain: {_domain}<br>Score: {score_value_mapping[score_value]}<br>Value: {domain_score_mapping[_domain][score_value]}',  # Set the hover text
                showlegend=True if idx == 0 else False,  # Show legend only for the first metric
            ))

    # change the background color
    _fig.update_layout(
        plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
    )

    # convert the plot to JSON format
    plot_json = pio.to_json(_fig)

    return plot_json

def ind_plot_5(_data):
    """
    Plot the fifth individual analysis plot of the data. 
    This plot specifically plots the hint reported scores (strategy wise).
    
    Args:
        _data (dict) : The plot data obtained from the utils.get_participant_details function.
    
    Returns:
        JSON string : The JSON string containing the plot data.
    """

    # get the color maps for the plot
    _, _, strategy_color_mapping, _ = obtain_plot_maps()

    # initialize a plotly figure to plot the data
    _fig = go.Figure()
    # update the layout of the figure
    _fig.update_layout(title={
                            'text': f"Total Hints asked (subjects)",
                            'y':0.98,
                            'x':0.45,
                        },
    )

    # plot the analysis on the hints feedback survey for the participant strategy-wise
    strategy_name_mapping = {0: 'random', 1: 'longest', 2: 'kmedoid', 3: 'dp'}
    score_value_mapping = {'1': "Strongly Dissatisfied", '2': "Dissatisfied", '3': "Neutral", '4': "Satisfied", '5': "Strongly Satisfied"}
    strategy_score_mapping = {strategy: {_k: 0 for _k in score_value_mapping.keys()} for strategy in strategy_name_mapping.values()}
    for q_no, question_responses in enumerate(_data['survey_responses']):
        for _idx, response in enumerate(_data['survey_responses'][q_no]):
            strategy_score_mapping[_data['hint_strategies'][q_no]][response['response']] += 1
    
    # Create a bar for each strategy for each score value
    for idx, score_value in enumerate(score_value_mapping.keys()):
        for _idx, strategy in enumerate(strategy_name_mapping.values()): # enumerate([0, 1, 2]):
            _fig.add_trace(go.Bar(
                x=[score_value_mapping[score_value]],  # Set the x value to the metric name
                y=[strategy_score_mapping[strategy][score_value]],  # Set the y value based on the metric
                name=strategy, # Set the trace name to the domain name
                marker_color=strategy_color_mapping[_idx],  # Set the bar color based on the domain
                offsetgroup=_idx,  # Use different offsetgroup for each domain
                hoverinfo='text',  # Set the hover info to text
                hovertext=f'Strategy: {strategy}<br>Score: {score_value_mapping[score_value]}<br>Value: {strategy_score_mapping[strategy][score_value]}',  # Set the hover text
                showlegend=True if idx == 0 else False,  # Show legend only for the first metric
            ))

    # change the background color
    _fig.update_layout(
        plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
    )

    # convert the plot to JSON format
    plot_json = pio.to_json(_fig)

    return plot_json

def ind_plot_5_v2(_data):
    """
    Plot the fifth individual analysis plot of the data. 
    This plot specifically plots the hint reported scores (strategy wise).
    
    Args:
        _data (dict) : The plot data obtained from the utils.get_participant_details function.
    
    Returns:
        JSON string : The JSON string containing the plot data.
    """

    # get the color maps for the plot
    _, _, _, strategy_color_mapping = obtain_plot_maps()

    # initialize a plotly figure to plot the data
    _fig = go.Figure()
    # update the layout of the figure
    _fig.update_layout(title={
                            'text': f"Hint Satisfaction ratings (offline-vs-online)",
                            'y':0.98,
                            'x':0.45,
                        },
    )

    # plot the analysis on the hints feedback survey for the participant strategy-wise
    score_value_mapping = {'1': "Strongly Dissatisfied", '2': "Dissatisfied", '3': "Neutral", '4': "Satisfied", '5': "Strongly Satisfied"}
    strategy_score_mapping = {strategy: {_k: 0 for _k in score_value_mapping.keys()} for strategy in strategy_color_mapping.keys()}
    for q_no, question_responses in enumerate(_data['survey_responses']):
        for _idx, response in enumerate(_data['survey_responses'][q_no]):
            strategy_score_mapping[_data['hint_strategies'][q_no]][response['response']] += 1
    
    # Create a bar for each strategy for each score value
    for idx, score_value in enumerate(score_value_mapping.keys()):
        for _idx, strategy in enumerate(strategy_color_mapping.keys()): # enumerate([0, 1, 2]):
            _fig.add_trace(go.Bar(
                x=[score_value_mapping[score_value]],  # Set the x value to the metric name
                y=[strategy_score_mapping[strategy][score_value]],  # Set the y value based on the metric
                name=strategy, # Set the trace name to the domain name
                marker_color=strategy_color_mapping[strategy],  # Set the bar color based on the domain
                offsetgroup=_idx,  # Use different offsetgroup for each domain
                hoverinfo='text',  # Set the hover info to text
                hovertext=f'Strategy: {strategy}<br>Score: {score_value_mapping[score_value]}<br>Value: {strategy_score_mapping[strategy][score_value]}',  # Set the hover text
                showlegend=True if idx == 0 else False,  # Show legend only for the first metric
            ))

    # change the background color
    _fig.update_layout(
        plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
    )

    # convert the plot to JSON format
    plot_json = pio.to_json(_fig)

    return plot_json

def ind_plot_6(_data):
    """
    Plot the sixth individual analysis plot of the data. 
    This plot specifically plots the action log of the participant.
    
    Args:
        _data (dict) : The plot data obtained from the utils.get_participant_details function.
    
    Returns:
        JSON string : The JSON string containing the plot data.
    """

    # get the color maps for the plot
    _, action_color_map, _, _ = obtain_plot_maps()

    # initialize a plotly figure to plot the data
    _fig = go.Figure()
    # update the layout of the figure
    _fig.update_layout(title={
                            'text': f"Participant's Quiz Journey. Hourglass denotes (>20secs).",
                            'y':0.98,
                            'x':0.45,
                        },
    )

    # flatten all the actions into a single list
    x_values, y_values, _symbols, _hovertext, _colors = [], [], [], [], []
    for q_no in range(_data['total_questions']):

        for action_no, action in enumerate(_data['actions'][q_no]):
            x_values.append(q_no)
            # if it is the first action, then subtract the start time of the question from the action time
            if action_no == 0:
                action_time = get_time_difference(action['timestamp'], _data['start_times'][q_no])
                y_value = action_time
            else:
                action_time = get_time_difference(action['timestamp'], _data['actions'][q_no][action_no - 1]['timestamp'])
                y_value = action_time + y_values[-1]
            
            # Cap an action's maximum time difference to 20 seconds
            # If the user spend over 20 seconds on an action, change it's marker for better visual representation
            if action_time > 20:
                y_values.append(20 + y_values[-1])
                _symbols.append('hourglass')
            else:
                y_values.append(y_value)
                _symbols.append('circle')
            
            # fix a typo in the database for the action 'stated question'. It should be 'started question'
            if action['action'] == 'stated question':
                action['action'] = 'started question'
            
            # add the hover text for the action
            if action['action'] == 'correct submission':
                _hovertext_detail = "<br>Submitted answer: " + action['detail'] + "<br>Correct answer: " + _data['answers'][q_no]
            elif action['action'] == 'wrong submission':
                _hovertext_detail = "<br>Submitted answer: " + action['attempted_answer'] + "<br>Correct answer: " + _data['answers'][q_no]
            elif action['action'] == 'hint requested': 
                _hovertext_detail = "<br>Hint: " + action['detail']
            else:
                _hovertext_detail = ""
            _hovertext.append("Action: " + action['action'] + _hovertext_detail +
                              f"<br>Time taken for the action: {action_time} seconds.<br>" +
                              f"Question: {_data['questions'][q_no]}<br>" +
                              f"Answer: {_data['answers'][q_no]}")

            # add the color for the action
            _colors.append(action_color_map[action['action']])

            # fix another bug in the database where multiple "survey completed" actions were logged.
            # break the loop if the action is "survey completed"
            if action['action'] == 'survey completed':
                break

    for action, color in action_color_map.items():
        # obtain the indices of the actions with the same color to plot them one color at a time
        indices = [idx for idx, _color in enumerate(_colors) if _color == color]
        _fig.add_trace(go.Scatter(
            x=[x_values[idx] for idx in indices],
            y=[y_values[idx] for idx in indices],
            mode='markers',
            marker=dict(
                size=10,
                symbol='star',
                line=dict(
                    width=1,
                    color='black',
                ),
            ),
            name=action,
            marker_color=[_colors[idx] for idx in indices],
            marker_symbol=[_symbols[idx] for idx in indices],
            hoverinfo='text',
            hovertext=[_hovertext[idx] for idx in indices],
        ))
    # Add axis labels
    _fig.update_xaxes(title_text="Question Number")
    _fig.update_yaxes(title_text="Time taken for all actions")

    # change the background color
    _fig.update_layout(
        plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
    )

    # convert the plot to JSON format
    plot_json = pio.to_json(_fig)

    return plot_json