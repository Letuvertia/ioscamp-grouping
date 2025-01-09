# Preference-Based Grouping
Group *N* people into teams of 5~7 based on their (unordered) preferences for teammates.

## Quick usage
```bash
python3 grouping.py
```

## Algorithm
See network as a directed graph, where people and their preferences are nodes and edges. To find teams in which people prefer each other is to find "communities" in the graph.

1. **Community Identification**: Apply the Girvan-Newman algorithm iteratively to partition the network into communities. Continue until all communities have a size less than 7 nodes.
1. **Merging Small Communities**: Identify communities with less than 5 nodes. These are considered "small communities."
    1. For each small community, evaluate potential merges with neighboring communities.
    1. Choose the neighboring community that results in the highest increase in modularity when merged.
    1. Perform the merge if the resulting community size stays below 7 nodes.
1. **Final Merging (Optional)**: If, after step 2, any communities still have less than 5 nodes, consider manually merging them with neighboring communities.

## An Example

Initial Network:

![](/fig/example_graph_before_girvan_newman.png)

Step 1: Community Identification (14 found)

![](/fig/example_graph_with_15_communities.png)

Step 2: Merge Small Community (7 communities after merging)

![](/fig/example_graph_with_merged_communities.png)

Result:
```
{1, 3, 6, 17, 22, 30}
{5, 40, 18, 26, 28, 31}
{32, 33, 16, 36, 38, 10}
{20, 21, 7, 27, 14}
{34, 19, 37, 39, 11}
{2, 35, 4, 9, 12, 13}
{23, 24, 8, 29, 25, 15}
```
