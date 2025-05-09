import json
import re
import os
import csv

def load_mapping(file_path="repository/cnn_com/mapping.csv"):
    filename_to_url = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 2:
                    filename, url = row[0].strip(), row[1].strip()
                    filename_to_url[filename] = url
    except Exception as e:
        print(f"Error loading mapping: {e}")
    return filename_to_url

def load_inverted_index(file_path="inverted_index.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_pagerank_scores(csv_path="repository/cnn_com/pagerank_top_100.csv"):
    pagerank_scores = {}
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) == 2:
                    url, score = row
                    pagerank_scores[url.strip()] = float(score.strip())
    except Exception as e:
        print(f"Error loading PageRank scores from CSV: {e}")
    return pagerank_scores


def tokenize_query(query):
    return re.findall(r'\b\w+\b', query.lower())

def boolean_search_with_scores(query, inverted_index):
    tokens = tokenize_query(query)
    if not tokens:
        return {}

    result_sets = []
    for token in tokens:
        if token in inverted_index:
            result_sets.append(set(inverted_index[token]))
        else:
            result_sets.append(set())  # Token not found

    relevant_docs = set.intersection(*result_sets) if result_sets else set()
    return {doc: 1.0 for doc in relevant_docs}  # Binary retrieval score

def combine_scores(retrieval_scores, pagerank_scores, filename_to_url, alpha=0.7, mode='multiply'):
    combined = {}

    for doc, r_score in retrieval_scores.items():
        doc_basename = os.path.basename(doc)
        url = filename_to_url.get(doc_basename)

        if url:
            p_score = pagerank_scores.get(url, 0.0)
        else:
            p_score = 0.0

        if mode == 'multiply':
            combined[doc] = (r_score * p_score) * 100  
        elif mode == 'linear':
            combined[doc] = alpha * r_score + (1 - alpha) * p_score

    return dict(sorted(combined.items(), key=lambda item: item[1], reverse=True))

def main():
    inverted_index = load_inverted_index()
    pagerank_scores = load_pagerank_scores()

    filename_to_url = load_mapping()

    print("Boolean AND Retrieval + PageRank Score Combination")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("> Enter your query: ")
        if query.lower() == "exit":
            break

        retrieval_scores = boolean_search_with_scores(query, inverted_index)
        if not retrieval_scores:
            print("No relevant results found.")
            continue

        combined = combine_scores(retrieval_scores, pagerank_scores, filename_to_url, alpha=0.7, mode='multiply')

        print("\nTop Combined Results (URLs):")
        for i, (doc, score) in enumerate(combined.items()):
            doc_basename = os.path.basename(doc)
            url = filename_to_url.get(doc_basename, f"[No URL found for {doc}]")
            print(f"{i+1}. {url} — Score: {score:.6f}")
            if i == 9:
                break
        print()

if __name__ == "__main__":
    main()
