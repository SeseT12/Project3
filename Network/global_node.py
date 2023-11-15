from Network.central_node import CentralNode
from Utils.np_encoder import NpEncoder
from Utils.packet_encoder import PacketEncoder
import threading
import socket
import numpy as np
import json


class GlobalNode:
    def __init__(self):
        self.networks = []
        self.network_id_increment = 0

    def add_network(self):
        new_network_id = 1 + self.network_id_increment
        create_network_thread = threading.Thread(target=self.create_network, args=(new_network_id,))
        create_network_thread.start()
        create_network_thread.join()

        self.networks.append(new_network_id)
        self.network_id_increment += 30

        self.distribute_adj_list(self.create_adj_list())

    def create_network(self, network_id):
        new_network = CentralNode(network_id)
        for i in range(5):
            new_network.add_node()

    def distribute_adj_list(self, adj_list):
        print(adj_list)
        for i in range(len(self.networks)):
            adj_list_json = json.dumps(adj_list, cls=NpEncoder)
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_socket.connect(('localhost', 30000 + self.networks[i]))
            send_socket.send(PacketEncoder.encode_adj_list_packet(adj_list_json.encode()))
            send_socket.shutdown(socket.SHUT_RDWR)
            send_socket.close()

    def create_adj_list(self):
        adj_list = {}
        for network_id in self.networks:
            adj_list[network_id] = []

        for i in range(len(self.networks)):
            for j in range(len(self.networks) - 1, i - 1, -1):
                if i != j:
                    #TODO: p values only for testing
                    connection = np.random.choice([0, 1], p=[0.1, 0.9])
                    if connection == 1:
                        adj_list[self.networks[i]].append(self.networks[j])
                        adj_list[self.networks[j]].append(self.networks[i])

        return adj_list
