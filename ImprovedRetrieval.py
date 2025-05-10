import json
import re

InvertedIndex = dict[str, list["InvertedIndexEntry"]]
class InvertedIndexEntry:
    file: str
    freq: int

    def __init__(self, entry):
        self.file = entry[0]
        self.freq = entry[1]

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return f"{self.file} -> {self.freq}"
    
    def __hash__(self):
        return self.file.__hash__()
    
    def __eq__(self, value):
        if isinstance(value, InvertedIndexEntry):
            return self.file == value.file
        else:
            return False

def load_inverted_index(file_path="inverted_index.json") -> InvertedIndex:
    with open(file_path, "r", encoding="utf-8") as f:
        j = json.load(f)
        inverted_index = { token: [InvertedIndexEntry(entry) for entry in entries] for token, entries in j.items() }
        return inverted_index

def tokenize_query(query: str) -> list[str]:
    return re.findall(r'\b\w+\b', query.lower())

def parse_query(query) -> str:
    ##supports: AND, OR, NOT 
    query = query.upper().replace("AND", "and").replace("OR", "or").replace("NOT", "not")
    return query

def evaluate_query(parsed_query: str, inverted_index: InvertedIndex):
    ##evaluate Boolean expressions 
    tokens = re.findall(r'\b\w+\b|and|or|not|\(|\)', parsed_query.lower())

    def resolve_term(token):
        return set(inverted_index.get(token, []))

    def evaluate(tokens):
        stack = []
        ops = []

        def apply_op():
            op = ops.pop()
            if op == 'not':
                term = stack.pop()
                all_docs = set(doc for doc_list in inverted_index.values() for doc in doc_list)
                stack.append(all_docs - term)
            else:
                right = stack.pop()
                left = stack.pop()
                if op == 'and':
                    res = left & right
                    s = set()
                    for r in res:
                        left_freq = next(index.freq for index in left if index.file == r.file)
                        right_freq = next(index.freq for index in right if index.file == r.file)
                        s.add(InvertedIndexEntry([r.file, min(left_freq, right_freq)]))
                    stack.append(s)
                elif op == 'or':
                    res = left | right
                    s = set()
                    for r in res:
                        left_freq = next((index.freq for index in left if index.file == r.file), 0)
                        right_freq = next((index.freq for index in right if index.file == r.file), 0)
                        s.add(InvertedIndexEntry([r.file, left_freq + right_freq]))
                    stack.append(s)

        for token in tokens:
            if token == '(':
                ops.append(token)
            elif token == ')':
                while ops and ops[-1] != '(':
                    apply_op()
                ops.pop()  #remove parenthesis
            elif token in ('and', 'or', 'not'):
                while ops and precedence(ops[-1]) >= precedence(token):
                    apply_op()
                ops.append(token)
            else:
                stack.append(resolve_term(token))

        while ops:
            apply_op()

        return stack[0] if stack else set()

    def precedence(op):
        return {'not': 3, 'and': 2, 'or': 1}.get(op, 0)

    return evaluate(tokens)

def main():
    inverted_index = load_inverted_index()

    print("\nImproved Retrieval Engine Ready (Supports AND, OR, NOT, parentheses)")
    while True:
        query = input("\n> Enter your query (type 'exit' to quit): ")
        if query.lower() == 'exit':
            break
        parsed_query = parse_query(query)
        results = evaluate_query(parsed_query, inverted_index)
        if results:
            print("Relevant documents:")
            for doc in sorted(results, key=lambda x: x.freq, reverse=True):
                print(f"  - {doc}")
        else:
            print("No relevant documents found.")

if __name__ == "__main__":
    main()
