import os
import json


def load_database_prompts(filename):
    """
    Loads JSON data containing database prompts from a specified file in the root directory of the project.

    Args:
        filename (str): The name of the JSON file containing the prompts.

    Returns:
        list: A list of dictionaries, where each dictionary represents a prompt.
    """
    try:
        # Get the root directory of the project
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

        # Construct the full filepath
        filepath = os.path.join(root_dir, 'project_config', filename)

        # Open the JSON file
        with open(filepath, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: File not found at '{filepath}'.")
        return None
