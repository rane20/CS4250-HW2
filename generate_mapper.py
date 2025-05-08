import os
import csv
from bs4 import BeautifulSoup
from urllib.parse import urlparse # urljoin is not strictly needed here but good for context

def find_canonical_or_base_url(file_path, file_directory_for_logging=""):
    """
    Parses an HTML file to find the canonical URL or base URL.
    Prefers canonical, then falls back to base.
    Returns the found URL (normalized by removing fragment) or None.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'lxml')

        found_url_str = None
        url_type = None

        # 1. Try to find link
        canonical_tag = soup.find('link', rel='canonical', href=True)
        if canonical_tag and canonical_tag['href'].strip():
            found_url_str = canonical_tag['href'].strip()
            url_type = "canonical"
        else:
            # 2. If no canonical, try to find <base href="...">
            base_tag = soup.find('base', href=True)
            if base_tag and base_tag['href'].strip():
                found_url_str = base_tag['href'].strip()
                url_type = "base"
        
        if found_url_str:
            parsed_url = urlparse(found_url_str)
            
            # Normalize the URL: remove fragment
            normalized_url = parsed_url._replace(fragment="").geturl()

            # Check if the URL is relative (lacks scheme and netloc)
            # A base URL can be relative, a canonical URL ideally should be absolute.
            if not parsed_url.scheme or not parsed_url.netloc:
                display_path = os.path.join(file_directory_for_logging, os.path.basename(file_path))
                print(f"  Warning: Found relative {url_type} URL '{normalized_url}' in '{display_path}'. Using as is.")
                print(f"           For best results with the PageRank script, this URL should ideally be absolute or resolvable.")

            return normalized_url
                
        return None # Neither canonical nor base URL found

    except FileNotFoundError:
        print(f"  Error: File not found at '{file_path}'")
        return None
    except Exception as e:
        display_path = os.path.join(file_directory_for_logging, os.path.basename(file_path))
        print(f"  Error parsing HTML file '{display_path}': {e}")
        return None

def create_mapping_csv_from_html(directory_path):
    """
    Iterates through HTML files in a directory, extracts canonical or base URLs,
    and writes them to mapping.csv.
    """
    if not os.path.isdir(directory_path):
        print(f"Error: '{directory_path}' is not a valid directory.")
        return

    mappings = []
    html_files_count = 0
    urls_extracted_count = 0

    print(f"Scanning directory: '{directory_path}' for HTML files...")

    # Iterate through all files and subdirectories
    for root, _, files in os.walk(directory_path):
        for filename in files:
            if filename.lower().endswith(('.html', '.htm')):
                html_files_count += 1
                file_path = os.path.join(root, filename)
                
                # For logging, show path relative to the initial directory_path
                relative_file_dir_for_log = os.path.relpath(root, directory_path)
                if relative_file_dir_for_log == ".":
                    relative_file_dir_for_log = ""

                print(f"Processing: '{os.path.join(relative_file_dir_for_log, filename)}'")
                
                # Pass the relative directory for clearer logging inside the function
                extracted_url = find_canonical_or_base_url(file_path, relative_file_dir_for_log)
                
                filename_for_csv = os.path.relpath(file_path, directory_path)

                if extracted_url:
                    mappings.append([filename_for_csv, extracted_url])
                    urls_extracted_count +=1
                    print(f"  Extracted ({'canonical' if 'canonical' in str(extracted_url).lower() else 'base'}): {extracted_url}") # Simple check
                else:
                    print(f"  Warning: No canonical or base URL found for '{filename_for_csv}'. This file will be skipped in mapping.csv.")

    if html_files_count == 0:
        print("No HTML files (.html, .htm) found in the directory or its subdirectories.")
        return

    if not mappings:
        print("No URLs could be extracted from the HTML files to create a mapping.csv.")
        return

    # Output CSV will be in the root of the input directory_path
    output_csv_path = os.path.join(directory_path, 'mapping.csv')
    
    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header for the CSV file
            writer.writerow(['filename', 'original_url']) 
            writer.writerows(mappings)
        print(f"\nSuccessfully created '{output_csv_path}'")
        print(f"Total HTML files scanned: {html_files_count}")
        print(f"URLs extracted and written to mapping.csv: {urls_extracted_count}")
    except Exception as e:
        print(f"\nError writing 'mapping.csv': {e}")

if __name__ == '__main__':
    target_directory = input("Enter the directory path containing your HTML files: ")
    create_mapping_csv_from_html(target_directory)
