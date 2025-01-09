import csv
import networkx as nx
import matplotlib.pyplot as plt
import random
import itertools

LAYOUT_SEED = 42
COLORS = [
    '#FFB3BA', '#FFDFBA', '#FFFFBA', '#BAFFC9', '#BAE1FF',
    '#FFB3E6', '#E6FFB3', '#E6B3FF', '#B3FFB3', '#FFCCE5',
    '#CCE5FF', '#E5FFCC', '#E5CCFF', '#CCFFE5', '#FFD1DC',
    '#D1FFD1', '#D1DCFF', '#FFDCB1', '#B1FFDC', '#FFB3FF'
]

def generate_graph_from_csv(file_path):
    graph = nx.DiGraph()
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            person = int(row[0])
            preferences = list(map(int, row[1:]))
            for preference in preferences:
                graph.add_edge(person, preference)
    return graph

def generate_graph_random(num_people=40, num_preferences=4):
    graph = nx.DiGraph()
    for person in range(1, num_people + 1):
        preferences = random.sample(range(1, num_people + 1), num_preferences)
        for preference in preferences:
            if person != preference:
                graph.add_edge(person, preference)
    return graph

def draw_graph(graph, title, filename):
    pos = nx.spring_layout(graph, seed=LAYOUT_SEED)
    plt.figure()
    nx.draw(graph, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size=500, font_size=10)
    plt.savefig(filename)
    plt.close()

def girvan_newman_algorithm(graph):
    comp = nx.community.girvan_newman(graph)
    return comp 

def draw_communities_on_graph(graph, communities, n_communities, filename):
    pos = nx.spring_layout(graph, seed=LAYOUT_SEED)
    plt.figure()
    nx.draw(graph, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size=500, font_size=10)
    
    for community, color in zip(communities, COLORS):
        nx.draw_networkx_nodes(graph, pos, nodelist=list(community), node_color=color)
    
    plt.savefig(filename)
    plt.close()

def merge_small_communities(graph, communities_original):
    communities = communities_original.copy()
    while True:
        small_communities = [c for c in communities if len(c) < 5]
        if not small_communities:
            break
        
        merge_at_least_once = False
        for small_community in small_communities:
            print(f'Try to find communities to merge with small community {small_community}')
            best_modularity_increase = -1
            best_merge = None
            for node in small_community:
                neighbors = set(graph.neighbors(node))
                for neighbor in neighbors:
                    for community in communities:
                        if neighbor in community and community != small_community and len(small_community | community) <= 6:
                            merged_community = small_community | community
                            new_communities = [c for c in communities if c != small_community and c != community] + [merged_community]
                            modularity_increase = nx.algorithms.community.quality.modularity(graph, new_communities) - nx.algorithms.community.quality.modularity(graph, communities)
                            if modularity_increase > best_modularity_increase:
                                best_modularity_increase = modularity_increase
                                best_merge = (small_community, community)
            
            if best_merge:
                print(f'Merging {best_merge[0]} and {best_merge[1]}')
                communities.remove(best_merge[0])
                communities.remove(best_merge[1])
                communities.append(best_merge[0] | best_merge[1])
                merge_at_least_once = True
                break
        
        if not merge_at_least_once:
            break
    
    return communities

def calculate_happiness(graph, communities):
    happiness = list()
    for community in communities:
        for node in community:
            happiness.append(sum(1 for neighbor in graph.neighbors(node) if neighbor in community))
    return happiness

if __name__ == "__main__":
    N = 40

    # Read or generate a graph
    # file_path = '/path/to/your/csvfile.csv'
    # graph = read_csv(file_path)
    graph = generate_graph_random()
    draw_graph(graph, 'Graph Before Girvan-Newman Algorithm', 'graph_before_girvan_newman.png')
    
    # Apply Girvan-Newman algorithm
    comp = girvan_newman_algorithm(graph)
    for n_communities, communities in enumerate(itertools.islice(comp, N), start=2):
        sorted(communities, key=len, reverse=True)
        draw_communities_on_graph(graph, communities, n_communities, f'graph_with_{n_communities}_communities.png')
        if (len(max(communities, key=len)) <= 6):
            break
    print(f'{n_communities} communities found:\n{communities}')

    # Merge small communities
    communities = list(communities)
    merged_communities = merge_small_communities(graph, communities)
    merged_communities = tuple(merged_communities)
    draw_communities_on_graph(graph, merged_communities, len(merged_communities), 'graph_with_merged_communities.png')
    print(f'Merged into {len(merged_communities)} communities:\n{merged_communities}')

    # Calcuate happiness
    happiness_list = calculate_happiness(graph, merged_communities)
    print(f'Average happiness: {sum(happiness_list) / len(happiness_list)}')  

    