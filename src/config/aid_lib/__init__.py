import json


def load_database_prompts(filepath):
    """
    Loads JSON data containing database prompts from a specified file path.

    Args:
        filepath (str): The path to the JSON file containing the prompts.

    Returns:
        list: A list of dictionaries, where each dictionary represents a prompt.
    """

    try:
        # Open the JSON file
        with open(filepath, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: File not found at '{filepath}'.")
        return None
