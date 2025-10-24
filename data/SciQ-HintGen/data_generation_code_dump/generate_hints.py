import os
import csv
import json
import tqdm
import openai
import asyncio
import pandas as pd

from load_data import load_data, convert_sciq_to_qa_pairs, convert_sciq_to_qa_context_pairs
from load_prompts import get_prompts
from call_openai import async_call_gpt

# global variables for the script
gpt4_prompts_path = "prompts/initial_prompts_gpt4.json"
prompts_path = "prompts/initial_prompts.json"
context_prompt_path = "prompts/context_prompts.json"
openai.api_key = "YOUR-API-KEY-HERE"


def run_gpt(prompts, qa_data, out_file_path, _model='gpt-3.5-turbo', _context=False):
    """
        A function that runs OpenAI's GPT models on the prompts and stores the results in the 'out_file_path' file.
    Args:
        prompts             : lorem ipsum
        _model(str)         : a string that can take values 'gpt-4', 'gpt-3.5-turbo'
        out_file_path (str) : output file path for a .json file where the dataset is stored.
    """

    # set this to the value None to run for the entire data
    data_size = None # 10 # None

    generated_data = []
            
    final_data = []

    # create a halt logic to resume from the last stopped point!
    # load the generated responses so far!
    start_point = {}
    for prompt_category in prompts:
        start_point[prompt_category['promptType']] = {}
        for prompt in prompt_category['prompts']:
            start_point[prompt_category['promptType']][prompt['id']] = 0

    if os.path.exists(out_file_path):
        gen_df = pd.read_csv(out_file_path, header=None)
        gen_df.columns = ['promptCategory', 'promptID', 'promptTemplate', 'question', 'answer', 'context', 'generatedHints']
        # prompt_categoty (zs/fs), prompt_id (zs1/zs2/etc), prompt_template, question, answer, context, generated_hints
        for prompt_category in prompts:
            for prompt in prompt_category['prompts']:
                start_point[prompt_category['promptType']][prompt['id']] = len(gen_df[ (gen_df['promptCategory'] == prompt_category['promptType']) & (gen_df['promptID'] == prompt['id']) ])

    print(f'start_point - {start_point}')
    
    # '''
    for prompt_category in prompts:

        print("Working on", prompt_category['promptType'], "prompts")
        category_data = []
        
        for prompt in tqdm.tqdm(prompt_category['prompts'], total=len(prompt_category['prompts']), position=0, leave=True):
            # store all the prompt calls for this prompt into one list
            messages = []
            print('Current prompt is - \n', prompt['prompt'])

            for inst in tqdm.tqdm(qa_data[start_point[prompt_category['promptType']][prompt['id']]:data_size], total=data_size, position=0, leave=True):
                curr_message = prompt['prompt']

                # replace the question and answer placeholders in the prompt
                curr_message = curr_message.replace('[question]', inst['question'])
                curr_message = curr_message.replace('[answer]', inst['answer'])
                if _context:
                    if len(inst['context']) == 0:
                        curr_message = curr_message.replace('[context]', 'Not available.')
                    curr_message = curr_message.replace('[context]', inst['context'])

                # print('Current query:', curr_message)

                messages.append(curr_message)
                
                """
                counter = 0
                response = 'QWERTY!'
                while counter < 20 and response == 'QWERTY!':
                    try:
                        counter += 1
                        chat = openai.ChatCompletion.create(model=_model, messages=[{"role": "user", "content": curr_message}])
                        response = chat.choices[0].message.content
                    except Exception as e:
                        response = 'QWERTY!'
                        print('Error occured:', e)
                
                # print('Generated Response: ', response)
                responses.append(response)
                """

            # """
            print('Calling GPT model')
            # print(messages, end='\n~~~\n')
            
            def chunks(lst, n):
                """Yield successive n-sized chunks from lst."""
                for i in range(0, len(lst), n):
                    yield lst[i:i + n]

            chunk_size = 10
            total_chunks = len(messages) // chunk_size if len(messages) % chunk_size == 0 else (len(messages) // chunk_size) + 1
            for chunk, _batch_data in tqdm.tqdm(zip(chunks(messages, chunk_size), chunks(qa_data[start_point[prompt_category['promptType']][prompt['id']]:data_size], chunk_size)), total=total_chunks, position=0, leave=True):
                curr_responses = asyncio.run(async_call_gpt(queries=chunk, engine=_model))
                curr_responses = [resp.choices[0].message.content for resp in curr_responses]
                # responses.extend(curr_responses)

                # save these responses into the corresponding file - 
                with open(out_file_path, 'a') as out_file:
                    writer = csv.writer(out_file)
                    for msg, inst, resp in zip(chunk, _batch_data, curr_responses):
                        # write row order - 
                        # prompt_categoty (zs/fs), prompt_id (zs1/zs2/etc), prompt_template, question, answer, context, generated_hints
                        writer.writerow([prompt_category['promptType'], prompt['id'], prompt['prompt'], inst['question'], inst['answer'], inst['context'], resp])

            # responses = [resp.choices[0].message.content for resp in responses]
            # """
            
            """
            print('Generated Responses: ', responses)

            prompt_data = []
            for inst, resp in zip(qa_data[:data_size], responses):
                prompt_data.append({'question': inst['question'], 'answer': inst['answer'], 'context': inst['context'], 'hints': resp})
            category_data.append({'id': prompt['id'], 'template': prompt['prompt'], 'instances': prompt_data})
        final_data.append({'promptType': prompt_category['promptType'], 'prompts': category_data})
    
    print('Saved at "', out_file_path, '"')
    with open(out_file_path, 'w') as out_file:
        json.dump(final_data, out_file)
    """
    # '''

if __name__ == "__main__":

    # load the sciq json dataset
    sciq_train, sciq_valid, sciq_test = load_data('SciQ')
    
    # load the zero-shot and few-shot prompts
    prompts = get_prompts(prompts_path)
    gpt4_prompts = get_prompts(gpt4_prompts_path)

    # run GPT4 on zs1 prompt! 
    # convert it to a dict with keys 'question', 'answer', 'context'
    for sciq_data, _split in zip([sciq_train, sciq_valid, sciq_test], ['train', 'valid', 'test']):

        sciq_qa_data  = convert_sciq_to_qa_context_pairs(sciq_data)
    
        print(f'Calling GPT4 for the {_split} split for zero- and few-shot prompts')
        # print(f'Calling GPT3.5-turbo for the {_split} split for zero- and few-shot prompts')

        # call the run_gpt model for gpt3.5-turbo
        run_gpt(gpt4_prompts, sciq_qa_data, f"generated_hints/{_split}_gpt4.csv", "gpt-4")
        # run_gpt(prompts, sciq_qa_data, f"generated_hints/{_split}_gpt35_turbo.csv", "gpt-3.5-turbo")

    # run GPT3.5-turbo on all the prompts!
    # convert it to a dict with keys 'question', 'answer', 'context'
    for sciq_data, _split in zip([sciq_train, sciq_valid, sciq_test], ['train', 'valid', 'test']):

        sciq_qa_data  = convert_sciq_to_qa_context_pairs(sciq_data)
    
        print(f'Calling GPT3.5-turbo for the {_split} split for zero- and few-shot prompts')

        # call the run_gpt model for gpt3.5-turbo
        run_gpt(prompts, sciq_qa_data, f"generated_hints/{_split}_gpt35_turbo.csv", "gpt-3.5-turbo")


    # load the zero-shot context prompt (that uses a context i.e. support as another input)
    context_prompts = get_prompts(context_prompt_path)
    
    # for sciq_data, _split in zip([sciq_train, sciq_valid, sciq_test], ['train', 'valid', 'test']):
    for sciq_data, _split in zip([sciq_train], ['train']):
    # for sciq_data, _split in zip([sciq_valid, sciq_test], ['valid', 'test']):

        sciq_qa_data  = convert_sciq_to_qa_context_pairs(sciq_data)

        print(f'Calling GPT3.5-turbo for the {_split} split for zero-shot context prompts')

        # call the run_gpt model for gpt3.5-turbo
        run_gpt(context_prompts, sciq_qa_data, f"generated_hints/{_split}_gpt35_turbo_context.csv", "gpt-3.5-turbo", _context=True)
