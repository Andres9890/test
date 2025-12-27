import internetarchive as ia
import os
import sys

def get_total_size(query):
    print(f"Fetching item list for query: '{query}'...")
    
    # search_items is a generator, so it's memory efficient
    search_results = ia.search_items(query, fields=['item_size'])

    total_bytes = 0
    item_count = 0

    for result in search_results:
        size = result.get('item_size')
        if size:
            total_bytes += int(size)
        item_count += 1

    return total_bytes, item_count

def format_size(size_bytes):
    # Helper to make bytes human readable
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

# --- usage ---

if __name__ == "__main__":
    # Get query from GitHub Action environment variable
    # Defaults to a placeholder if run locally without env vars
    SEARCH_QUERY = os.getenv('INPUT_QUERY', 'uploader:jscott@archive.org')

    if SEARCH_QUERY == 'uploader:jscott@archive.org':
        print("Using default placeholder query.")

    total_size, count = get_total_size(SEARCH_QUERY)

    print(f"--- RESULTS ---")
    print(f"Query: {SEARCH_QUERY}")
    print(f"Total Items: {count}")
    print(f"Total Size:  {format_size(total_size)}")
    
    # Set output for next steps in GitHub Actions
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            fh.write(f"total_items={count}\n")
            fh.write(f"readable_size={format_size(total_size)}\n")