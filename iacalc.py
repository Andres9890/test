import internetarchive as ia
import os
import sys

def get_size_stats(query):
    print(f"Fetching item list for query: '{query}'...")
    
    # We need to fetch 'identifier' now as well
    search_results = ia.search_items(query, fields=['item_size', 'identifier'])

    total_bytes = 0
    item_count = 0
    
    # Initialize metrics
    # Set min to infinity so the first item will always be smaller
    min_bytes = float('inf')
    max_bytes = 0
    
    # Initialize identifier trackers
    min_id = "N/A"
    max_id = "N/A"

    for result in search_results:
        size = result.get('item_size')
        identifier = result.get('identifier')
        
        if size:
            size_int = int(size)
            total_bytes += size_int
            
            # Update Max
            if size_int > max_bytes:
                max_bytes = size_int
                max_id = identifier
            
            # Update Min
            if size_int < min_bytes:
                min_bytes = size_int
                min_id = identifier
                
        item_count += 1

    # Calculate Average and handle empty results
    if item_count > 0:
        avg_bytes = total_bytes / item_count
        # If min_bytes is still infinity, set to 0
        if min_bytes == float('inf'):
            min_bytes = 0
            min_id = "N/A"
    else:
        avg_bytes = 0
        min_bytes = 0

    return {
        "total": total_bytes,
        "count": item_count,
        "max": max_bytes,
        "max_id": max_id,
        "min": min_bytes,
        "min_id": min_id,
        "avg": avg_bytes
    }

def format_size(size_bytes):
    # Helper to make bytes human readable
    if size_bytes == 0:
        return "0 B"
        
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

# --- usage ---

if __name__ == "__main__":
    # Get query from GitHub Action environment variable
    SEARCH_QUERY = os.getenv('INPUT_QUERY', 'uploader:jscott@archive.org')

    if SEARCH_QUERY == 'uploader:jscott@archive.org':
        print("Using default placeholder query.")

    stats = get_size_stats(SEARCH_QUERY)

    print(f"--- RESULTS ---")
    print(f"Query:       {SEARCH_QUERY}")
    print(f"Total Items: {stats['count']}")
    print(f"Total Size:  {format_size(stats['total'])}")
    print(f"Largest:     {format_size(stats['max'])} ({stats['max_id']})")
    print(f"Smallest:    {format_size(stats['min'])} ({stats['min_id']})")
    print(f"Average:     {format_size(stats['avg'])}")
    
    # Set output for next steps in GitHub Actions
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            fh.write(f"total_items={stats['count']}\n")
            fh.write(f"readable_size={format_size(stats['total'])}\n")
            fh.write(f"readable_max={format_size(stats['max'])}\n")
            fh.write(f"max_identifier={stats['max_id']}\n")
            fh.write(f"readable_min={format_size(stats['min'])}\n")
            fh.write(f"min_identifier={stats['min_id']}\n")
            fh.write(f"readable_avg={format_size(stats['avg'])}\n")
