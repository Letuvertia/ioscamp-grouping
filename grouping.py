import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
import random
import itertools
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

matplotlib.rcParams['font.sans-serif'] = ['Noto Sans TC'] # set traditional Chinese font
LAYOUT_SEED = 42
COLORS = [
    '#FFB3BA', '#FFDFBA', '#FFFFBA', '#BAFFC9', '#BAE1FF',
    '#FFB3E6', '#E6FFB3', '#E6B3FF', '#B3FFB3', '#FFCCE5',
    '#CCE5FF', '#E5FFCC', '#E5CCFF', '#CCFFE5', '#FFD1DC',
    '#D1FFD1', '#D1DCFF', '#FFDCB1', '#B1FFDC', '#FFB3FF'
]

id_to_name = dict()

def read_from_google_sheet(sheet_id, path_to_credentials) -> pd.DataFrame:
    # Define the scope
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # Add credentials to the account
    creds = ServiceAccountCredentials.from_json_keyfile_name(path_to_credentials, scope)

    # Authorize the clientsheet 
    client = gspread.authorize(creds)

    # Get the instance of the Spreadsheet
    sheet = client.open_by_key(sheet_id)

    # Get the first sheet of the Spreadsheet
    worksheet = sheet.get_worksheet(0)

    # Get all the records of the data
    records = worksheet.get_all_values()
    records_df = pd.DataFrame(records[1:], columns=records[0])

    return records_df

def generate_graph_google_sheet(sheet_id='1HC7UZAEg7BJ9sD29Ufvdzpa3FCp3Bw72ZMzI5C126XA',
                                path_to_credentials='api-keys/ioscamp-grouping-df344bc23626.json') -> nx.DiGraph:
    records_df = read_from_google_sheet(sheet_id, path_to_credentials)
    print(f'{records_df.shape[0]} reponses in total')
    print(records_df)
    
    def parse_id(id_and_name):
        id = id_and_name.split('. ')[0]
        name = id_and_name.split('. ')[1]
        id_to_name[id] = name
        return id
    
    graph = nx.DiGraph()
    for index, row in records_df.iterrows():
        # Access values by column name
        person_id = parse_id(row['請選擇您的名字與學員編號'])
        for perference_id in [parse_id(id_and_name) for id_and_name in row['請勾選您希望與其同組的學員'].split(', ')]:
            if person_id != perference_id:
                graph.add_edge(person_id, perference_id)
    return graph

def generate_graph_random(num_people=40, num_preferences=4) -> nx.DiGraph:
    graph = nx.DiGraph()
    for person in range(1, num_people + 1):
        preferences = random.sample(range(1, num_people + 1), num_preferences)
        for preference in preferences:
            if person != preference:
                graph.add_edge(person, preference)
    return graph

def draw_graph(graph, title, filename):
    pos = nx.spring_layout(graph, seed=LAYOUT_SEED, k=0.3, iterations=30)
    plt.figure()
    labels = {node: id_to_name[node] for node in graph.nodes()}
    nx.draw(graph, pos, with_labels=True, labels=labels, node_color='lightblue', edge_color='gray', node_size=600, font_size=8)
    plt.savefig(filename, dpi=600)
    plt.close()

def girvan_newman_algorithm(graph):
    comp = nx.community.girvan_newman(graph)
    return comp 

def draw_communities_on_graph(graph, communities, n_communities, filename):
    pos = nx.spring_layout(graph, seed=LAYOUT_SEED, k=0.3, iterations=30)
    plt.figure()
    labels = {node: id_to_name[node] for node in graph.nodes()}
    nx.draw(graph, pos, with_labels=True, labels=labels, node_color='lightblue', edge_color='gray', node_size=600, font_size=8)
    for community, color in zip(communities, COLORS):
        nx.draw_networkx_nodes(graph, pos, nodelist=list(community), node_color=color)
    plt.savefig(filename, dpi=600)
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

def replace_id_with_name(communities) -> tuple:
    if id_to_name:
        return tuple([{f'{id}. {id_to_name[id]}' for id in community} for community in communities])
    else:
        return communities

if __name__ == "__main__":
    N = 40
    DATA_SOURCE = 'google_sheet'

    if DATA_SOURCE == 'google_sheet':
        graph = generate_graph_google_sheet()
        draw_graph(graph, 'Graph Before Girvan-Newman Algorithm', 'graph_before_girvan_newman.png')
    elif DATA_SOURCE == 'random':
        graph = generate_graph_random()
        draw_graph(graph, 'Graph Before Girvan-Newman Algorithm', 'graph_before_girvan_newman.png')
    
    # Apply Girvan-Newman algorithm
    comp = girvan_newman_algorithm(graph)
    for n_communities, communities in enumerate(itertools.islice(comp, N), start=2):
        sorted(communities, key=len, reverse=True)
        draw_communities_on_graph(graph, communities, n_communities, f'graph_with_{n_communities}_communities.png')
        if (len(max(communities, key=len)) <= 7):
            break
    print(f'{n_communities} communities found:\n{replace_id_with_name(communities)}')

    # Merge small communities
    communities = list(communities)
    merged_communities = merge_small_communities(graph, communities)
    merged_communities = tuple(merged_communities)
    draw_communities_on_graph(graph, merged_communities, len(merged_communities), 'graph_with_merged_communities.png')
    print(f'Merged into {len(merged_communities)} communities:\n{replace_id_with_name(merged_communities)}')
    for i, community in enumerate(merged_communities):
        print(f'第{i + 1}組：')
        for person in community:
            print(f'{person}. {id_to_name[person]}')
        print()

    # Calcuate happiness
    happiness_list = calculate_happiness(graph, merged_communities)
    print(f'Average happiness: {sum(happiness_list) / len(happiness_list)}')  

    