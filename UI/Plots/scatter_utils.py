import re
import ast
import plotly.io as pio
import plotly.graph_objs as go

def obtain_scatter_plot(question_data):
    """
    A function to obtain the informativeness scatter plot.
    
    Args:
        question_data (dict) : a dictionary containing the similarity scores between question, answer, context and hints.
                                          It also contains the topic modelling responses and the informativeness score.
                                          It also contains the question data - {question, answer, hints, context, domain}
    
    Returns:
        JSON string : The JSON string containing the plot data.
    """
    answer_hint_similarities = question_data['answer_similarity']
    question_hint_similarities = question_data['question_similarity']
    context_hint_similarities = question_data['context_similarity']
    info_score = question_data['informativeness_score']
    hover_text_topics = question_data['topics'].split('\n')
    hint_topics_dict = {hint: ast.literal_eval('[' + topic_map + ']') for hint, topic_map in question_data['hint_topic_mapping'].items()}
    total_topics = 5 # hard-coded for now

    all_hints = question_data['hints'] # process_hints(question_data['hints'])

    # Map hints to topics based on the topic with the highest probability
    # If the highest affinity is below a threshold, assign the hint to a separate topic
    hint_topic_mapping = {}
    for i, hint in enumerate(all_hints):
        hint_dict = [(idx, prob) for idx, prob in enumerate(hint_topics_dict[hint])]

        max_affinity_topic = max(hint_dict, key=lambda x: x[1])[0]
        if max(hint_dict, key=lambda x: x[1])[1] < 0.35:
            hint_topic_mapping[hint] = total_topics
        else:
            hint_topic_mapping[hint] = max_affinity_topic

    def get_hover_text(hint, hint_prompt_dict):
        txt = hint + '<br>'
        txt += 'Question similarity: {:.2f}'.format(question_hint_similarities[hint]) + '<br>'
        txt += 'Answer similarity: {:.2f}'.format(answer_hint_similarities[hint]) + '<br>'
        txt += 'Context similarity: {:.2f}'.format(context_hint_similarities[hint]) + '<br>'
        txt += 'Informativeness score: {:.2f}'.format(info_score[hint]) + '<br>'
        txt += 'Topic: {}'.format(hint_topics_dict[hint]) + '<br>'
        txt += 'Generation Prompt: {}'.format(hint_prompt_dict[hint])
        return txt

    def get_plot_utils(_hints):
        _relevance_score = [context_hint_similarities[hint] for hint in _hints]
        _info_score = {k: v for k, v in info_score.items() if k in _hints}
        _info_score_list = list(_info_score.values())
        _sizes = {hint: len(hint) for hint in all_hints}
        _normalized_sizes = {hint: (x-min(_sizes.values()))*(30-10)/(max(_sizes.values())-min(_sizes.values()))+10 for hint, x in _sizes.items()}
        _normalized_sizes = [_normalized_sizes[hint] for hint in _hints]
        hint_prompt_dict = get_hint_prompt_dict(question_data['raw_hints'])
        _hover_text = [get_hover_text(hint, hint_prompt_dict) for hint in _hints]
        return _info_score_list, _relevance_score, _normalized_sizes, _hover_text

    # identify the irrelevant hints
    irrelevance_threshold = 0.2
    irrelevant_hints = [hint for hint in question_hint_similarities if question_hint_similarities[hint] < irrelevance_threshold and answer_hint_similarities[hint] < irrelevance_threshold]
    relevant_hints = [hint for hint in all_hints if hint not in irrelevant_hints]

    # Define the colors for the topics
    colors = ['mediumorchid', 'mediumseagreen', 'peachpuff', 'dodgerblue', 'crimson', 'snow']  # add more colors if you have more topics

    # Map each hint to a color based on its topic
    hint_color_mapping = {hint: colors[topic] for hint, topic in hint_topic_mapping.items()}

    # Create a figure
    fig = go.Figure()

    # if there are any relevant hints, plot them
    if len(relevant_hints) > 0:
        relevant_info_score_list, context_relevance_scores, relevant_normalized_sizes, relevant_hover_text = get_plot_utils(relevant_hints)
        relevant_colors = [hint_color_mapping[hint] for hint in relevant_hints]
        # Add a scatter plot to the figure (for relevant hints)
        fig.add_trace(go.Scatter(
            x = relevant_info_score_list,  # x-axis values
            y=[i for i in context_relevance_scores],  # y-axis values
            mode='markers',
            name='Relevant Hints',
            text=relevant_hover_text,  # text to show when hovering over a point
            hoverinfo='text',
            marker=dict(
                size=relevant_normalized_sizes,  # increase dot size
                color=relevant_colors,  # set dot color
                line=dict(
                    color='black',  # set border color
                    width=2  # set border width
                )
            )
        ))
    
    if len(irrelevant_hints) > 0:
        irrelevant_info_score_list, context_relevance_scores, irrelevant_normalized_sizes, irrelevant_hover_text = get_plot_utils(irrelevant_hints)
        # Add a scatter plot to the figure (for irrelevant hints)
        fig.add_trace(go.Scatter(
            x = irrelevant_info_score_list,  # x-axis values
            y=[-abs(i) for i in context_relevance_scores],  # y-axis values
            mode='markers',
            name='Irrelevant Hints',
            text=irrelevant_hover_text,  # text to show when hovering over a point
            hoverinfo='text',
            marker=dict(
                size=irrelevant_normalized_sizes,  # increase dot size
                color='red',  # set dot color
                line=dict(
                    color='black',  # set border color
                    width=2  # set border width
                )
            )
        ))

    # Add a scatter plot to the figure for each topic
    for i in range(total_topics):
        fig.add_trace(go.Scatter(
            x=[0.35 + 0.1*i],  # adjust these values as needed
            y=[1.1],  # adjust these values as needed
            mode='markers',
            name='Topic {}'.format(i),
            hoverinfo='text',
            hovertext=[hover_text_topics[i]],
            marker=dict(
                size=25,  # adjust as needed
                color=colors[i],  # color corresponding to the topic
                symbol='star'
            )
        ))

    def get_wrapped_text(_text, crop=True):
        if _text is None:
            return 'None'
        if crop:
            _text = _text[:200]
        temp = '<br>'.join(_text[i:i+100] for i in range(0, len(_text), 100))
        if crop and len(_text) > 200:
            temp += '...'
        return temp

    plot_title = "Question: " + get_wrapped_text(question_data['question'], crop=False) + "<br>" + "Answer: '" + question_data['answer'] + "' / " + "Total hints: " + str(len(all_hints)) + " / " + "Domain: " + question_data['domain'] + " / Embedding Model: " + question_data['embed_model'] + "<br>" + "Context: " + get_wrapped_text(question_data['context'])


    # Change the background color and add a title
    fig.update_layout(
        plot_bgcolor='aliceblue',  # set background color
        xaxis_title="Informativeness Score", # set x-axis label
        yaxis_title="Context Relevance Score", # set y-axis label
        title={
            'text': plot_title, 
            'y': 0.95,  # Adjust the y position to add margin
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'pad': {'t': 5},  # Add padding to the top
            'font': {'size': 14},  # Change the font size
        },
        margin={'t': 20 + plot_title.count('<br>') * 25}  # Add margin to the top of the plot
    )

    # change the background color
    fig.update_layout(
        plot_bgcolor='rgba(245, 245, 245, 1)',  # Change the plot background color to white
    )

    # convert the plot to JSON format
    plot_json = pio.to_json(fig)

    return plot_json


def process_hints(hints):
    """ A function to process the hints generated by the model.
    Args:
        hints (list of str): hints generated by the model.
    Returns:
        hints (list of str): processed hints.
    """
    final_hints = []
    for hint in hints:
        # hint = hint.strip()
        # hint = hint.split('\t')[-1]
        hint = re.sub(r'^[-+]?[0-9]+. ', '', hint)
        hint = re.sub(r'^[-+]?[0-9]+\) ', '', hint)
        hint = re.sub(r'^Hint [-+]?[0-9]+: ', '', hint)
        hint = re.sub(r'^Hint[-+]?[0-9]+: ', '', hint)
        hint = re.sub('Hint: ', '', hint)
        final_hints.append(hint)
    return final_hints

def get_hint_prompt_dict(raw_hints):
    """
    A function obtain the hint-prompt dict (used in genrating hints).

    Args:
        raw_hints (str): raw hints generated by the model.
    
    Returns:
        hint_prompt_dict (dict): hint-prompt dict
    """
    hint_prompt_dict = {}
    for _hint in raw_hints.split('\n'):
        hint = _hint.strip().split('\t')[-1]
        hint = hint.split('\t')[-1]
        hint = re.sub(r'^[-+]?[0-9]+. ', '', hint)
        hint = re.sub(r'^[-+]?[0-9]+\) ', '', hint)
        hint = re.sub(r'^Hint [-+]?[0-9]+: ', '', hint)
        hint = re.sub(r'^Hint[-+]?[0-9]+: ', '', hint)
        hint = re.sub('Hint: ', '', hint)
        hint_prompt_dict[hint] = _hint.strip().split('\t')[1] + ' - ' + _hint.strip().split('\t')[2] + ' - ' + _hint.strip().split('\t')[3]
    
    return hint_prompt_dict