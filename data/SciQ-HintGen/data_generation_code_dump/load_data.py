import os
import json

# change this path
sciq_data_path = "../../SciQ"

def load_sciq(dir_path, split='train'):
    file_path = os.path.join(dir_path, split + '.json')

    with open(file_path, 'r') as _file:
        data = json.load(_file)

    return data


def load_data(data_name):

    if data_name == 'SciQ':
        train_data = load_sciq(sciq_data_path, 'train')
        valid_data = load_sciq(sciq_data_path, 'valid')
        test_data  = load_sciq(sciq_data_path, 'test')
    # if data_name == '':
    else:
        print("Wrong data name provided. Pass one of the following dataset names - 'SciQ'.")

    return train_data, valid_data, test_data


def convert_sciq_to_qa_pairs(_data):
    """
        A function to convert the sciq dataset into a {'question': ..., 'answer': ...} format dataset for run_gpt function.
    Args:
        _data: one split of the sciq dataset comprising of the following keys - ('question', 'wrong choice 1/2/3', 'correct_answer', 'context')
    """
    new_data = []
    for inst in _data:
        new_data.append({'question': inst['question'], 'answer': inst['correct_answer']})

    return new_data


def convert_sciq_to_qa_context_pairs(_data):
    """
        A function to convert the sciq dataset into a {'question': ..., 'answer': ...} format dataset for run_gpt function.
    Args:
        _data: one split of the sciq dataset comprising of the following keys - ('question', 'wrong choice 1/2/3', 'correct_answer', 'context')
    """
    new_data = []
    for inst in _data:
        new_data.append({'question': inst['question'], 'answer': inst['correct_answer'], 'context': inst['support']})

    return new_data


if __name__ == "__main__":
    train_data, valid_data, test_data = load_data('SciQ')

    for idx, inst in enumerate(train_data[:11]):
        print(idx, ':', inst)
