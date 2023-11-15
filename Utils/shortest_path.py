from collections import deque

def get_next_node(start_node, end_node, adj_list):
    next_node = None
    current_min_distance = float('inf')
    for neighbor_node in adj_list.get(start_node):
        distance = get_distance(neighbor_node, end_node, adj_list)
        if distance != -1 and distance < current_min_distance:
            next_node = neighbor_node

    return next_node



def get_distance(start_node, end_node, adj_list):
    distances = {node: -1 for node in adj_list.keys()}
    distances[start_node] = 0

    queue = deque([start_node])
    while queue:
        current_node = queue.popleft()
        for neighbor in adj_list[current_node]:
            if distances[neighbor] == -1:
                distances[neighbor] = distances[current_node] + 1
                queue.append(neighbor)

    return distances[end_node]
