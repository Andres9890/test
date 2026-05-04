import heapq
import internetarchive as ia
import os
import sys

def get_size_stats(query):
    print(f"Fetching item list for query: '{query}'...")
    
    # We need to fetch 'identifier' now as well
    search_results = ia.search_items(query, fields=['item_size', 'identifier'])

    total_bytes = 0
    item_count = 0
    
    # Top 3 smallest: max-heap via negative size (heapq is min-heap)
    smallest_heap = []
    # Top 3 largest: min-heap of (size, identifier)
    largest_heap = []

    for result in search_results:
        size = result.get('item_size')
        identifier = result.get('identifier')
        
        if size:
            size_int = int(size)
            total_bytes += size_int

            if len(smallest_heap) < 3:
                heapq.heappush(smallest_heap, (-size_int, identifier))
            elif size_int < -smallest_heap[0][0]:
                heapq.heapreplace(smallest_heap, (-size_int, identifier))

            if len(largest_heap) < 3:
                heapq.heappush(largest_heap, (size_int, identifier))
            elif size_int > largest_heap[0][0]:
                heapq.heapreplace(largest_heap, (size_int, identifier))
                
        item_count += 1

    smallest_three = sorted((-neg_sz, ident) for neg_sz, ident in smallest_heap)
    largest_three = sorted(largest_heap, key=lambda x: x[0], reverse=True)

    if smallest_three:
        min_bytes, min_id = smallest_three[0]
        max_bytes, max_id = largest_three[0]
    else:
        min_bytes, min_id = 0, "N/A"
        max_bytes, max_id = 0, "N/A"

    if item_count > 0:
        avg_bytes = total_bytes / item_count
    else:
        avg_bytes = 0

    return {
        "total": total_bytes,
        "count": item_count,
        "max": max_bytes,
        "max_id": max_id,
        "min": min_bytes,
        "min_id": min_id,
        "avg": avg_bytes,
        "smallest_three": smallest_three,
        "largest_three": largest_three,
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
    print(f"3 smallest (by item size):")
    if stats["smallest_three"]:
        for sz, ident in stats["smallest_three"]:
            print(f"  - {format_size(sz)} ({ident})")
    else:
        print("  (no items with size)")
    print(f"3 largest (by item size):")
    if stats["largest_three"]:
        for sz, ident in stats["largest_three"]:
            print(f"  - {format_size(sz)} ({ident})")
    else:
        print("  (no items with size)")

    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        lines = [
            "## Internet Archive size calculator",
            "",
            f"- **Query:** `{SEARCH_QUERY}`",
            f"- **Total items:** {stats['count']}",
            f"- **Total size:** {format_size(stats['total'])}",
            f"- **Average:** {format_size(stats['avg'])}",
            "",
            "### 3 smallest (by item size)",
            "",
        ]
        if stats["smallest_three"]:
            lines.extend(f"- {format_size(sz)} (`{ident}`)" for sz, ident in stats["smallest_three"])
        else:
            lines.append("*No items with size.*")
        lines.extend(["", "### 3 largest (by item size)", ""])
        if stats["largest_three"]:
            lines.extend(f"- {format_size(sz)} (`{ident}`)" for sz, ident in stats["largest_three"])
        else:
            lines.append("*No items with size.*")
        lines.append("")
        with open(summary_path, "a", encoding="utf-8") as sh:
            sh.write("\n".join(lines))
    
    # Set output for next steps in GitHub Actions
    if os.getenv('GITHUB_OUTPUT'):
        def _write_heredoc(name, lines):
            with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
                out.write(f"{name}<<EOF\n")
                out.write("\n".join(lines))
                out.write("\nEOF\n")

        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            fh.write(f"total_items={stats['count']}\n")
            fh.write(f"readable_size={format_size(stats['total'])}\n")
            fh.write(f"readable_max={format_size(stats['max'])}\n")
            fh.write(f"max_identifier={stats['max_id']}\n")
            fh.write(f"readable_min={format_size(stats['min'])}\n")
            fh.write(f"min_identifier={stats['min_id']}\n")
            fh.write(f"readable_avg={format_size(stats['avg'])}\n")
        _write_heredoc(
            "smallest_three",
            [f"{format_size(sz)} ({ident})" for sz, ident in stats["smallest_three"]],
        )
        _write_heredoc(
            "largest_three",
            [f"{format_size(sz)} ({ident})" for sz, ident in stats["largest_three"]],
        )
