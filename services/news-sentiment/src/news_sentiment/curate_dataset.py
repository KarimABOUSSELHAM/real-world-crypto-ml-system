import json

from loguru import logger
from opik import Opik


def mark_item_as_correct(dataset, item):
    """
    Marks data item as correct in the dataset logged in opik by adding a new column
    called `is_human_checked` and setting it to True
    """
    # Apparently there is no a direct approach to update dataset inside opik.
    # Therefore, the way to do so is to delete the data and insert it again.
    dataset.delete([item['id']])
    new_item = {
        **item,
        'is_human_checked': True,
    }
    dataset.insert([new_item])


def ask_human_for_correction(dataset, item):
    """
    Asks the human to provide the correct version of the output's field:
    - expected_output (which needs to be a valid list of Json)
    - expected_reason (which needs to be a valid string saying why you chose such output)
    """
    # Ask the user to provide the expected output and validate it as a list of Json
    while True:
        expected_output = input(
            'Please provide the expected output as a list of Json: '
        )
        try:
            expected_output = json.loads(expected_output)
            break
        except json.JSONDecodeError:
            print('Invalid Json, please try again!')
            continue
    # Ask the user to provide the expected reason and validate it as a string
    while True:
        expected_reason = input('Please provide the expected reason as a string: ')
        if expected_reason:
            break
        else:
            print('Invalid string, please try again!')
            continue
    #  Update the item with the new data
    item['expected_output'] = expected_output
    item['expected_reason'] = expected_reason
    mark_item_as_correct(dataset=dataset, item=item)


def curate_dataset(dataset_name: str):
    """
    Curates the dataset with a human in the loop
    """
    # Load the dataset we want to curate
    logger.info(f'Start curating the dataset {dataset_name}')
    client = Opik()
    dataset = client.get_or_create_dataset(name=dataset_name)
    dataset_items = json.loads(dataset.to_json())
    dataset_items = [
        item for item in dataset_items if not item.get('is_human_verified', False)
    ]
    logger.info(
        f'loaded {len(dataset_items)} items for the dataset that are not human verified'
    )
    for item in dataset_items:
        print('**-----------------------------------------**')
        print(f'input: {item["input"]}')
        print('-----------------------------------------')
        print(f'expected output: {item["expected_output"]}')
        print('-----------------------------------------')
        print(f'expected reason: {item["expected_reason"]}')
        print('-----------------------------------------')
        print(f'teacher model: {item["teacher_model"]}')
        print('**-----------------------------------------**')
        #  Ask the user whether the item is correct or not
        is_correct: str = input('Is the item correct? (y/n): ')
        while True:
            if is_correct.lower() in ('y', 'yes'):
                mark_item_as_correct(dataset, item)
                # print("Item is correct")
                break
            elif is_correct.lower() in ('n', 'no'):
                ask_human_for_correction(dataset, item)
                break
            else:
                print('Invalid input')
                continue


if __name__ == '__main__':
    from fire import Fire

    Fire(curate_dataset)
