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

def main():
    """
    Main function to count quotes in a file.
    """
    print("Counting quotes in quotes.json...")    
    filename = 'quotes.json'
    quote_count = count_quotes(filename)
    print(f"Number of quotes in {filename}: {quote_count}")

if __name__ == "__main__":
    main()