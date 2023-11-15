import random
from Network.forwarding_information_base import ForwardingInformationBase
from Network.node import Node
import numpy as np
import threading
import socket
import json
import time

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

class CentralNode:
    def __init__(self, network_id):
        self.network_id = network_id
        self.node_id_increment = 1
        self.nodes = []

    def add_node(self):
        new_node_port = 30000 + self.network_id + self.node_id_increment
        new_node_id = self.network_id + self.node_id_increment
        threading.Thread(target=self.create_node, args=(new_node_port, new_node_id, self.network_id)).start()
        #new_node = Node(new_node_port, new_node_id, self.network_id)

        self.nodes.append(self.network_id + self.node_id_increment)
        self.node_id_increment += 1

        adj_matrix = self.create_adj_matrix()
        #self.distribute_adj_matrix(adj_matrix)
        self.distribute_fib(adj_matrix)

    def create_node(self, port, id, network_id):
        new_node = Node(port, id, network_id)
        new_node.start()

    def distribute_adj_matrix(self, adj_matrix):
        for i in range(len(self.nodes)):
            print("distribute adj")
            #self.nodes.get(self.network_id + i + 1).adj_matrix = adj_matrix

    def distribute_fib(self, adj_matrix):
        time.sleep(1)
        for i in range(len(self.nodes)):
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_socket.connect(('localhost', 30000 + self.network_id + i + 1))
            send_socket.send(json.dumps(self.create_fib(adj_matrix, i).entries, cls=NpEncoder).encode())
            send_socket.shutdown(socket.SHUT_RDWR)
            send_socket.close()
            #self.nodes.get(self.network_id + i + 1).fib = self.create_fib(adj_matrix, i)

    def create_adj_matrix(self):
        adj_matrix = np.zeros((len(self.nodes), len(self.nodes)), np.uint8)
        for i in range(len(self.nodes)):
            for j in range(len(self.nodes) - 1, i - 1, -1):
                if i != j:
                    connection = np.random.choice([0, 1], p=[0.4, 0.6])
                    adj_matrix[i][j] = connection
                    adj_matrix[j][i] = connection

        return adj_matrix

    def create_fib(self, adj_matrix, node_index):
        fib = ForwardingInformationBase()
        for index in range(len(adj_matrix[node_index])):
            if index != node_index:
                name_prefix = "network" + str(self.network_id) + "/" + str(index + 1 + self.network_id) + "/"
                forwarding_nodes = self.find_paths_to_node(adj_matrix, node_index, index)
                if len(forwarding_nodes) > 0:
                    fib.add_entry(name_prefix, forwarding_nodes)

        return fib

    def find_paths_to_node(self, adj_matrix, from_node_index, to_node_index):
        path_nodes = []
        for index in np.where(adj_matrix[from_node_index] == 1)[0]:
            if index == to_node_index:
                path_nodes.append(index)
            elif self.path_exists(adj_matrix, index, to_node_index, [from_node_index]):
                path_nodes.append(index)

        return path_nodes

    def path_exists(self, adj_matrix, from_node_index, to_node_index, visited):
        path_exists = False
        for index in np.where(adj_matrix[from_node_index] == 1)[0]:
            if index not in visited:
                if index == to_node_index:
                    return True
                visited.append(index)
                path_exists = path_exists | self.path_exists(adj_matrix, index, to_node_index, visited)

        return path_exists
