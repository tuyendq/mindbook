from datetime import datetime
from contextlib import contextmanager

@contextmanager
def timer():
    start = datetime.now()
    yield
    end = datetime.now()
    print(f"It took {end-start} to complete.")

def count_quotes(filename: str) -> int:
    """
    Counts the number of quotes in a file.

    Args:
        filename (str): The path to the file containing quotes.

    Returns:
        int: The number of quotes in the file.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
            return content.count('author')
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return 0
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0

import json
def update_quotes(filename: str, new_quote: dict = {}) -> None:
    """
    Updates the total number of quotes.

    Args:
        filename (str): The path to the file containing quotes.
    """
    try:
        with open(filename, 'r+', encoding='utf-8') as file:
            quotes = json.load(file)
            if not isinstance(quotes, dict):
                raise ValueError("Quotes file must contain a dictionary.")
            number_of_quotes = len(quotes.get("quotes", []))
            quotes["total_quotes"] = number_of_quotes
            # Move the file pointer to the beginning before writing
            file.seek(0)
            json.dump(quotes, file, indent=4, ensure_ascii=False)
            file.truncate()
    except FileNotFoundError:
        print(f"File {filename} not found. Creating a new one.")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    """
    Main function to count quotes in a file.
    """
    print("Counting quotes in quotes.json...")    
    filename = 'quotes.json'
    # with timer():
    #     quote_count = count_quotes(filename)
    # print(f"Number of quotes in {filename}: {quote_count}")
    with timer():
        update_quotes(filename)


if __name__ == "__main__":
    main()