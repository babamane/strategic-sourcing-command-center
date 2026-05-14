from tools.tavily_search_tool import tavily_search
import json

# Run the search
query = "Give me price insight of Microsoft if they have increase/decrease prices of their any tool/product or services"
print(f"Running Tavily search with query: {query}\n")
print("=" * 80)

result = tavily_search.invoke(query)

# Save to file
output_file = "tavily_search_results.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print("\nSearch Results:")
print("=" * 80)
print(json.dumps(result, indent=2))
print("=" * 80)
print(f"\nSearch completed successfully!")
print(f"Results saved to: {output_file}")
