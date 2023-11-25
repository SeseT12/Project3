# Contributor(s): sregitz
from Network.central_node import CentralNode
from Utils.np_encoder import NpEncoder
from Utils.packet_encoder import PacketEncoder
import threading
import socket
import numpy as np
import json


class GlobalNode:
    def __init__(self):
        self.network_ids = []
        self.central_nodes = []
        self.network_id_increment = 0

    def add_network(self):
        new_network_id = 1 + self.network_id_increment
        central_node = CentralNode(new_network_id)
        self.central_nodes.append(central_node)
        create_network_thread = threading.Thread(target=self.create_network, args=(central_node,))
        create_network_thread.start()
        create_network_thread.join()

        self.network_ids.append(new_network_id)
        self.network_id_increment += 30

        self.distribute_adj_list(self.create_adj_list())
        for central_node in self.central_nodes:
            print(central_node.network_adj_list)

    def create_network(self, central_node):
        central_node.start()
        for i in range(5):
            central_node.add_node()

    def distribute_adj_list(self, adj_list):
        """""""""
        print("Global Adj" + str(adj_list))
        for i in range(len(self.network_ids)):
            adj_list_json = json.dumps(adj_list, cls=NpEncoder)
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_socket.connect(('localhost', 33000 + self.network_ids[i]))
            send_socket.send(PacketEncoder.encode_adj_list_packet(adj_list_json.encode()))
            send_socket.shutdown(socket.SHUT_RDWR)
            send_socket.close()
        """""""""
        for i in range(len(self.network_ids)):
            self.central_nodes[i].network_adj_list = adj_list
            self.central_nodes[i].distribute_fib()

    def create_adj_list(self):
        adj_list = {}
        for network_id in self.network_ids:
            adj_list[network_id] = []

        for i in range(len(self.network_ids)):
            for j in range(len(self.network_ids) - 1, i - 1, -1):
                if i != j:
                    #TODO: p values only for testing
                    connection = np.random.choice([0, 1], p=[0.1, 0.9])
                    if connection == 1:
                        adj_list[self.network_ids[i]].append(self.network_ids[j])
                        adj_list[self.network_ids[j]].append(self.network_ids[i])

        return adj_list
