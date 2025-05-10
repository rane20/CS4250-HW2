# Part2: Simple Retrieval 
import json
import re

# Load the inverted index json file
def load_inverted_index(file_path="inverted_index.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# tokenize and lowercase
def tokenize_query(query):
    return re.findall(r'\b\w+\b', query.lower())

# Boolean AND retrieval
def boolean_search(query, inverted_index):
    tokens = tokenize_query(query)
    
    if not tokens:
        return []

    result_sets = []
    for token in tokens:
        if token in inverted_index:
            result_sets.append(set(t[0] for t in inverted_index[token]))
        else:
            result_sets.append(set())  # No results for this term

    # Intersect all sets (AND operation)
    relevant_docs = set.intersection(*result_sets) if result_sets else set()
    return sorted(relevant_docs)

def main():
    inverted_index = load_inverted_index()

    while True:
        query = input("\n> Please enter your query (or type 'exit' to quit): ")
        if query.lower() == "exit":
            break
        results = boolean_search(query, inverted_index)
        if results:
            print(f"Relevant results are: {', '.join(results)}")
        else:
            print("No relevant results found.")

if __name__ == "__main__":
    main()
