# Part1 contuinued: Indexing
import os
import json
from bs4 import BeautifulSoup
from collections import defaultdict
import re

def extract_clean_text(html_path):
    with open(html_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")
        return soup.get_text(separator=" ", strip=True)

def tokenize(text):
    return re.findall(r'\b\w+\b', text.lower())

def build_inverted_index(base_repo_path="repository"):
    inverted_index = defaultdict()  

    for crawler_folder in os.listdir(base_repo_path):
        domain_path = os.path.join(base_repo_path, crawler_folder)
        if os.path.isdir(domain_path):
            for filename in os.listdir(domain_path):
                if filename.endswith(".html"):
                    file_path = os.path.join(domain_path, filename)
                    text = extract_clean_text(file_path)
                    tokens = tokenize(text)
                    for token in set(tokens):
                        if token not in inverted_index:
                            inverted_index[token] = []
                        inverted_index[token].append([f"{crawler_folder}/{filename}", tokens.count(token)]) #returns page and which domain it's from 

    inverted_index = {term: sorted(list(files)) for term, files in inverted_index.items()}

    with open("inverted_index.json", "w", encoding="utf-8") as f:
        json.dump(inverted_index, f, indent=2, ensure_ascii=False)

    print("Inverted index built and saved to 'inverted_index.json'.")

if __name__ == "__main__":
    build_inverted_index()
