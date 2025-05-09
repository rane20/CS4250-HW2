import json
import re

def load_inverted_index(file_path="inverted_index.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def tokenize_query(query):
    return re.findall(r'\b\w+\b', query.lower())

def parse_query(query):
    ##supports: AND, OR, NOT 
    query = query.upper().replace("AND", "and").replace("OR", "or").replace("NOT", "not")
    return query

def evaluate_query(parsed_query, inverted_index):
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
                    stack.append(left & right)
                elif op == 'or':
                    stack.append(left | right)

        i = 0
        while i < len(tokens):
            token = tokens[i]
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
            i += 1

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
            for doc in sorted(results):
                print(f"  - {doc}")
        else:
            print("No relevant documents found.")

if __name__ == "__main__":
    main()
