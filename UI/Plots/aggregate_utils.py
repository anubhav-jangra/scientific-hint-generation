import plotly.io as pio
import plotly.graph_objs as go

# Define the color maps for all the plots
def obtain_plot_maps(num_participants):
    blue_colors = ['SlateBlue', 'Teal', 'Azure', 'Cyan', 'LightCyan', 'PaleTurquoise', 'Aquamarine', 'Turquoise', 'MediumTurquoise', 'DarkTurquoise', 'CadetBlue', 'SteelBlue', 'LightSteelBlue', 'PowderBlue', 'LightBlue', 'SkyBlue', 'LightSkyBlue', 'DeepSkyBlue', 'DodgerBlue', 'CornflowerBlue', 'AliceBlue', 'MediumSlateBlue', 'RoyalBlue', 'Blue', 'MediumBlue', 'DarkBlue', 'Navy', 'MidnightBlue', 'Indigo'] * 3  # Repeat to ensure enough colors for participants
    participant_color_mapping = {f"P-{i+1}": blue_colors[i] for i in range(num_participants)}
    strategy_color_mapping_old = {0: 'Bisque', 1: 'SandyBrown', 2: 'Chocolate', 3: 'Brown'}
    strategy_color_mapping_new = {'no-hint': 'SandyBrown', 'offline': 'Chocolate', 'online': 'Brown'}
    domain_color_mapping = {'physics': 'Orchid', 'chemistry': 'Magenta', 'biology': 'RebeccaPurple', 'earth science': 'DarkViolet'} # , 'miscellaneous': 'Lavender'}

    # strategy_name_mapping = {0: 'Random', 1: 'Longest', 2: 'Ours'}
    strategy_name_mapping = {0: 'random', 1: 'longest', 2: 'kmedoid', 3: 'dp'}

    return participant_color_mapping, strategy_color_mapping_old, strategy_color_mapping_new, domain_color_mapping, strategy_name_mapping

def agg_plot_1(_data):
    """
    Plot the first aggregate analysis plot of the data. 
    This plot specifically plots the individual's performance in the quiz.
    Plotting the number of correct answers, number of skipped questions, and the total time spent on the quiz.
    
    Args:
        _data (dict) : The plot data obtained from the utils.get_participant_details function.
    
    Returns:
        JSON string : The JSON string containing the plot data.
    """

    # obtain the color maps for the plots
    participant_color_mapping, _, _, _, _ = obtain_plot_maps(len(_data))

    # initialize a plotly figure to plot the data
    _fig = go.Figure()
    # update the layout of the figure
    _fig.update_layout(title={
                            'text': f"Participant's Invididual Performance",
                            'y':0.98,
                            'x':0.45,
                        },
    )

    # plot different performance metrics for each participant
    _metrics = ['correctly_answered', 'skipped_question', 'total_time_spent']
    metric_name_mapping = {'correctly_answered': 'Correct Answers', 'skipped_question': 'Skipped Questions', 'total_time_spent': 'Total Time Spent (in minutes)'}
    for j, _metric in enumerate(_metrics):
        for idx, (participant_id, participant_data) in enumerate(_data.items()):
            _fig.add_trace(go.Bar(x=[metric_name_mapping[_metric]], 
                                  y=[sum(participant_data[_metric]) if _metric != 'total_time_spent' else sum(participant_data[_metric]) / 60],
                                  name=participant_id, 
                                  offsetgroup=idx,
                                  marker_color=participant_color_mapping[participant_id], 
                                  hoverinfo='text',  # Set the hover info to text
                                  hovertext=f'Participant: {participant_id}<br>' + 
                                             f'{metric_name_mapping[_metric]}: {sum(participant_data[_metric]) if _metric != 'total_time_spent' else sum(participant_data[_metric]) / 60: .2f}<br>', # Set the hover text
                                  showlegend=True if j == 0 else False,  # Show legend only for the first metric
                            ))

    # Set the bar mode to 'group' and change the background color
    _fig.update_layout(
        barmode='group',
        plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
    )

    # convert the plot to JSON format
    plot_json = pio.to_json(_fig)

    return plot_json

def agg_plot_2(_data):
    """
    Plot the second aggregate analysis plot of the data. 
    This plot specifically plots the individual's self-reported confidence across subjects.
    
    Args:
        _data (dict) : The plot data obtained from the utils.get_participant_details function.
    
    Returns:
        JSON string : The JSON string containing the plot data.
    """

    # obtain the color maps for the plots
    participant_color_mapping, _, _, _, _ = obtain_plot_maps(len(_data))

    # initialize a plotly figure to plot the data
    _fig = go.Figure()
    # update the layout of the figure
    _fig.update_layout(title={
                            'text': f"Participant's Self Confidence",
                            'y':0.98,
                            'x':0.45,
                        },
    )

    for idx, (participant_id, participant_data) in enumerate(_data.items()):
        for j, domain in enumerate(['physics', 'chemistry', 'biology', 'earth_sciences']):
            _fig.add_trace(go.Bar(x=[domain], 
                                  y=[participant_data['subject_confidence'][domain]], 
                                  name=participant_id, 
                                  offsetgroup=idx, 
                                  marker_color=participant_color_mapping[participant_id], 
                                  hoverinfo='text',  # Set the hover info to text
                                  hovertext=f'Participant: {participant_id}<br>' + 
                                             f'Subject: {domain}<br>' + 
                                             f'Self Reported Confidence (1-5 scale): {participant_data['subject_confidence'][domain]: .2f}<br>', # Set the hover text
                                  showlegend=True if j == 0 else False,  # Show legend only for the first metric
                            ))
            
    # Set the bar mode to 'group' and change the background color
    _fig.update_layout(
        barmode='group',
        plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
    )

    # convert the plot to JSON format
    plot_json = pio.to_json(_fig)

    return plot_json

def agg_plot_3(_data):
    """
    Plot the third aggregate analysis plot of the data. 
    This plot specifically plots the subject-wise hint score distribution for each participant.
    
    Args:
        _data (dict) : The plot data obtained from the utils.get_participant_details function.
    
    Returns:
        JSON string : The JSON string containing the plot data.
    """
    # obtain the color maps for the plots
    _, _, _, domain_color_mapping, _ = obtain_plot_maps(len(_data))

    # initialize a plotly figure to plot the data
    _fig = go.Figure()
    # update the layout of the figure
    _fig.update_layout(title={
                            'text': f"Hint score distribution (subject-wise)",
                            'y':0.98,
                            'x':0.45,
                        },
    )

    score_value_mapping = {'1': "Strongly Dissatisfied", '2': "Dissatisfied", '3': "Neutral", '4': "Satisfied", '5': "Strongly Satisfied"}
    domain_score_mapping = {domain: {_k: 0 for _k in score_value_mapping.keys()} for domain in domain_color_mapping.keys()}
    for domain in domain_color_mapping.keys():
          for idx, (participant_id, participant_data) in enumerate(_data.items()):
            for q_no, question_responses in enumerate(participant_data['survey_responses']):
                if participant_data['question_domain_mapping'][participant_data['questions'][q_no]] == domain:
                    for _idx, response in enumerate(participant_data['survey_responses'][q_no]):
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

    # Set the bar mode to 'group' and change the background color
    _fig.update_layout(
        barmode='group',
        plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
    )

    # convert the plot to JSON format
    plot_json = pio.to_json(_fig)

    return plot_json

def agg_plot_4(_data):
    """
    Plot the fourth aggregate analysis plot of the data. 
    This plot specifically plots the subject-wise hint score distribution for each participant.
    
    Args:
        _data (dict) : The plot data obtained from the utils.get_participant_details function.
    
    Returns:
        JSON string : The JSON string containing the plot data.
    """

    # obtain the color maps for the plots
    _, strategy_color_mapping, _, _, strategy_name_mapping = obtain_plot_maps(len(_data))

    # initialize a plotly figure to plot the data
    _fig = go.Figure()
    # update the layout of the figure
    _fig.update_layout(title={
                            'text': f"Hint score distribution (baseline-wise)",
                            'y':0.98,
                            'x':0.45,
                        },
    )

    score_value_mapping = {'1': "Strongly Dissatisfied", '2': "Dissatisfied", '3': "Neutral", '4': "Satisfied", '5': "Strongly Satisfied"}
    strategy_score_mapping = {strategy: {_k: 0 for _k in score_value_mapping.keys()} for strategy in strategy_name_mapping.values()}
    for idx, (participant_id, participant_data) in enumerate(_data.items()):
        for q_no, question_responses in enumerate(participant_data['survey_responses']):
            for _idx, response in enumerate(participant_data['survey_responses'][q_no]):
                strategy_score_mapping[participant_data['hint_strategies'][q_no]][response['response']] += 1
    
    # Create a bar for each strategy for each score value
    for idx, score_value in enumerate(score_value_mapping.keys()):
        for _idx, strategy in enumerate(strategy_name_mapping.values()):
            _fig.add_trace(go.Bar(
                x=[score_value_mapping[score_value]],  # Set the x value to the metric name
                y=[strategy_score_mapping[strategy][score_value]],  # Set the y value based on the metric
                name=strategy,  # Set the trace name to the domain name
                marker_color=strategy_color_mapping[_idx],  # Set the bar color based on the domain
                offsetgroup=_idx,  # Use different offsetgroup for each domain
                hoverinfo='text',  # Set the hover info to text
                hovertext=f'Strategy: {strategy}<br>Score: {score_value_mapping[score_value]}<br>Value: {strategy_score_mapping[strategy][score_value]}',  # Set the hover text
                showlegend=True if idx == 0 else False,  # Show legend only for the first metric
            ))
    
    # Set the bar mode to 'group' and change the background color
    _fig.update_layout(
        barmode='group',
        plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
    )

    # convert the plot to JSON format
    plot_json = pio.to_json(_fig)

    return plot_json

def agg_plot_4_new(_data):
    """
    Plot the fourth aggregate analysis plot of the data for new evaluation setting (offline vs online).
    This plot specifically plots the subject-wise hint score distribution for each participant.
    
    Args:
        _data (dict) : The plot data obtained from the utils.get_participant_details function.
    
    Returns:
        JSON string : The JSON string containing the plot data.
    """

    # obtain the color maps for the plots
    _, _, strategy_color_mapping_new, _, _ = obtain_plot_maps(len(_data))
    # drop the 'no-hint' strategy from the color mapping (as there's no survey for it)
    strategy_color_mapping_new.pop('no-hint', None)

    # initialize a plotly figure to plot the data
    _fig = go.Figure()
    # update the layout of the figure
    _fig.update_layout(title={
                            'text': f"Hint score distribution (baseline-wise)",
                            'y':0.98,
                            'x':0.45,
                        },
    )

    score_value_mapping = {'1': "Strongly Dissatisfied", '2': "Dissatisfied", '3': "Neutral", '4': "Satisfied", '5': "Strongly Satisfied"}
    strategy_score_mapping = {strategy: {_k: 0 for _k in score_value_mapping.keys()} for strategy in strategy_color_mapping_new.keys()}
    for idx, (participant_id, participant_data) in enumerate(_data.items()):
        for q_no, question_responses in enumerate(participant_data['survey_responses']):
            for _idx, response in enumerate(participant_data['survey_responses'][q_no]):
                strategy_score_mapping[participant_data['hint_strategies'][q_no]][response['response']] += 1
    
    # Create a bar for each strategy for each score value
    for idx, score_value in enumerate(score_value_mapping.keys()):
        for _idx, strategy in enumerate(strategy_color_mapping_new.keys()):
            _fig.add_trace(go.Bar(
                x=[score_value_mapping[score_value]],  # Set the x value to the metric name
                y=[strategy_score_mapping[strategy][score_value]],  # Set the y value based on the metric
                name=strategy,  # Set the trace name to the domain name
                marker_color=strategy_color_mapping_new[strategy],  # Set the bar color based on the domain
                offsetgroup=_idx,  # Use different offsetgroup for each domain
                hoverinfo='text',  # Set the hover info to text
                hovertext=f'Strategy: {strategy}<br>Score: {score_value_mapping[score_value]}<br>Value: {strategy_score_mapping[strategy][score_value]}',  # Set the hover text
                showlegend=True if idx == 0 else False,  # Show legend only for the first metric
            ))
    
    # Set the bar mode to 'group' and change the background color
    _fig.update_layout(
        barmode='group',
        plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
    )

    # convert the plot to JSON format
    plot_json = pio.to_json(_fig)

    return plot_json

# def agg_plot_5(_data):
#     """
#     Plot the fifth aggregate analysis plot of the data.
#     This plot specifically plots the section-level survey responses for each participant.
    
#     Args:
#         _data (dict) : The plot data obtained from the utils.get_participant_details function.
    
#     Returns:
#         JSON string : The JSON string containing the plot data.
#     """
#     # obtain the color maps for the plots
#     _, _, strategy_color_mapping_new, _, _ = obtain_plot_maps(len(_data))

#     # initialize a plotly figure to plot the data
#     _fig = go.Figure()
#     # update the layout of the figure
#     _fig.update_layout(title={
#                             'text': f"Quiz Section Difficulty",
#                             'y':0.98,
#                             'x':0.45,
#                         },
#     )

    
#     metric_name_mapping = {'correctly_answered': 'Correct Answers', 'skipped_question': 'Skipped Questions', 'total_time_spent': 'Total Time Spent (in minutes)'}
#     for j, _metric in enumerate(strategy_color_mapping_new.keys()):
#         for idx, (participant_id, participant_data) in enumerate(_data.items()):
#             _fig.add_trace(go.Bar(x=[metric_name_mapping[_metric]], 
#                                   y=[sum(participant_data[_metric]) if _metric != 'total_time_spent' else sum(participant_data[_metric]) / 60],
#                                   name=participant_id, 
#                                   offsetgroup=idx,
#                                   marker_color=participant_color_mapping[participant_id], 
#                                   hoverinfo='text',  # Set the hover info to text
#                                   hovertext=f'Participant: {participant_id}<br>' + 
#                                              f'{metric_name_mapping[_metric]}: {sum(participant_data[_metric]) if _metric != 'total_time_spent' else sum(participant_data[_metric]) / 60: .2f}<br>', # Set the hover text
#                                   showlegend=True if j == 0 else False,  # Show legend only for the first metric
#                             ))

#     # Set the bar mode to 'group' and change the background color
#     _fig.update_layout(
#         barmode='group',
#         plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
#     )

#     # convert the plot to JSON format
#     plot_json = pio.to_json(_fig)

#     return plot_json