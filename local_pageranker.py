import os
import csv
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import networkx as nx
import collections

def load_url_mapping(directory_path):
    """
    Assumes a 'mapping.csv' file in the directory_path.
    Format: filename,original_url
    """
    filename_to_url = {}
    url_to_filename = {}
    mapping_file_path = os.path.join(directory_path, 'mapping.csv')

    if not os.path.exists(mapping_file_path):
        print(f"Error: 'mapping.csv' not found in {directory_path}")
        print("Please create it with two columns: filename,original_url")
        return None, None

    try:
        with open(mapping_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # next(reader) # Uncomment this if your CSV has a header row
            for row in reader:
                if len(row) == 2:
                    filename, original_url = row[0].strip(), row[1].strip()
                    # Basic normalization for lookup: ensure scheme, remove fragment
                    parsed_url = urlparse(original_url)
                    normalized_url = parsed_url._replace(fragment="").geturl()
                    
                    filename_to_url[filename] = normalized_url
                    url_to_filename[normalized_url] = filename
                else:
                    print(f"Warning: Skipping malformed row in mapping.csv: {row}")
    except Exception as e:
        print(f"Error reading mapping.csv: {e}")
        return None, None
        
    return filename_to_url, url_to_filename

def build_link_graph(directory_path, filename_to_url, url_to_filename):
    """
    Builds a directed graph from links between local HTML files.
    """
    graph = nx.DiGraph()

    if not filename_to_url or not url_to_filename:
        return None

    for filename in filename_to_url.keys():
        graph.add_node(filename)

    for filename in filename_to_url.keys():
        file_path = os.path.join(directory_path, filename)
        base_url = filename_to_url.get(filename)

        if not base_url:
            print(f"Warning: No original URL found for {filename} in mapping. Skipping.")
            continue

        if not os.path.exists(file_path):
            print(f"Warning: HTML file {file_path} not found. Skipping.")
            continue
        
        print(f"Processing {filename} (Original: {base_url})")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'lxml') # 'lxml' is a fast parser

            for link_tag in soup.find_all('a', href=True):
                href = link_tag['href']
                
                # Resolve the relative or absolute href to a full URL
                absolute_target_url = urljoin(base_url, href)
                
                # Normalize the target URL for lookup (remove fragment, etc.)
                parsed_target_url = urlparse(absolute_target_url)
                normalized_target_url = parsed_target_url._replace(fragment="").geturl()

                # Check if this target URL corresponds to a known local file
                if normalized_target_url in url_to_filename:
                    target_filename = url_to_filename[normalized_target_url]
                    if filename != target_filename:
                        graph.add_edge(filename, target_filename)
                # else:
                    # print(f"  Ignoring external link: {normalized_target_url}")

        except Exception as e:
            print(f"Error processing file {filename}: {e}")
            continue
            
    return graph

def main():
    directory_path = input("Enter the directory path containing HTML files and mapping.csv: ")

    if not os.path.isdir(directory_path):
        print(f"Error: Directory not found: {directory_path}")
        return

    print("Step 1: Loading URL mappings...")
    filename_to_url, url_to_filename = load_url_mapping(directory_path)

    if not filename_to_url:
        return

    print(f"\nStep 2: Building link graph from {len(filename_to_url)} HTML files...")
    link_graph = build_link_graph(directory_path, filename_to_url, url_to_filename)

    if not link_graph:
        print("Failed to build the link graph.")
        return
    
    if not link_graph.nodes():
        print("Graph has no nodes. Ensure mapping.csv and HTML files are correct.")
        return

    print(f"\nGraph built with {link_graph.number_of_nodes()} nodes and {link_graph.number_of_edges()} edges.")

    print("\nStep 3: Calculating PageRank...")
    try:
        # NetworkX's default damping factor (alpha) is 0.85
        pagerank_scores_filenames = nx.pagerank(link_graph)
    except Exception as e:
        print(f"Error calculating PageRank: {e}")
        if link_graph.number_of_nodes() > 0 and link_graph.number_of_edges() == 0:
            print("Hint: The graph has nodes but no edges. This might happen if no internal links were found.")
        return

    # Map filenames back to original URLs for the results
    pagerank_scores_urls = {}
    for filename, score in pagerank_scores_filenames.items():
        original_url = filename_to_url.get(filename, f"Unknown URL for {filename}")
        pagerank_scores_urls[original_url] = score
    
    # Sort by PageRank score in descending order
    sorted_pagerank = sorted(pagerank_scores_urls.items(), key=lambda item: item[1], reverse=True)

    print("\nStep 4: Writing top 100 results to CSV...")
    output_csv_path = os.path.join(directory_path, 'pagerank_top_100.csv')
    
    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Original URL', 'PageRank Score']) # Header
            for i, (url, score) in enumerate(sorted_pagerank):
                if i < 100:
                    writer.writerow([url, score])
    except Exception as e:
        print(f"Error writing CSV to {output_csv_path}: {e}")
        return

    print(f"\nProcessing complete. Top 100 PageRank scores saved to: {output_csv_path}")
    if len(sorted_pagerank) > 0:
        print("\nTop 5 pages:")
        for i, (url, score) in enumerate(sorted_pagerank):
            if i < 5:
                print(f"{i+1}. {url}: {score:.6f}")
            else:
                break
    else:
        print("No PageRank scores were calculated.")

if __name__ == '__main__':
    main()