import random
from Network.forwarding_information_base import ForwardingInformationBase
from Network.node import Node
from Network.interest_packet import InterestPacket
from Network.data_packet import DataPacket
from Network.pending_interest_table import PendingInterestTable
from Network.content_store import ContentStore
from Utils.tlv_types import TLVType
from Utils.np_encoder import NpEncoder
from Utils.json_keys_to_int import json_keys_to_int
from Utils.shortest_path import get_next_node
from Utils.packet_encoder import PacketEncoder
import numpy as np
import threading
import socket
import json
import select
import time


class CentralNode:
    def __init__(self, network_id):
        self.network_id = network_id
        self.node_id_increment = 1
        self.node_ids = []
        self.nodes = []

        self.content_store = ContentStore()
        self.pit = PendingInterestTable()

        self.node_adj_matrix = []
        self.network_adj_list = {}

        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.init_server()
        #self.start()

    def init_server(self):
        """Initialization of the TCP/IP server to receive connections. It binds to the given host and port."""
        print("Initialisation of the Router on port: " + str(33000 + self.network_id))
        self.receive_socket.bind(('', 33000 + self.network_id))
        self.receive_socket.settimeout(10.0)
        self.receive_socket.listen(1)

    def start(self):
        threading.Thread(target=self.run).start()
        threading.Thread(target=self.simulate_movement).start()

    def run(self):
        try:
            print("Node: Wait for incoming connection")

            while True:
                readable, _, _ = select.select([self.receive_socket], [], [], 10.0)

                if self.receive_socket in readable:
                    connection, client_address = self.receive_socket.accept()
                    data = connection.recv(1024)
                    if data:
                        threading.Thread(target=self.receive_message, args=(data,)).start()

        except Exception as e:
            raise e

    def receive_message(self, data):
        # TODO: works for interest + data packet, move to tlv
        tlv_data = InterestPacket.decode_tlv(data)
        if TLVType.INTEREST_PACKET in tlv_data:
            print("Received Interest Packet")
            self.process_interest(data)
        if TLVType.DATA_PACKET in tlv_data:
            print("Received Data Packet")
            self.process_data_packet(data, tlv_data)
        if TLVType.ADJ_LIST in tlv_data:
            self.process_adj_list_packet(tlv_data)
            # self.fib.entries = json.loads(data.decode())

    def process_interest(self, interest_packet):
        tlv_data = InterestPacket.decode_tlv(interest_packet)
        if self.content_store.entry_exists(interest_packet):
            if tlv_data[TLVType.ID] in self.nodes:
                self.send_data(interest_packet)
            else:
                network_id = int(tlv_data[TLVType.NAME_COMPONENT].decode().split("/")[0].split("network")[1])
                if network_id != self.network_id:
                    next_network_router_id = get_next_node(self.network_id, network_id, self.network_adj_list)
                    if next_network_router_id is not None:
                        self.send_data(interest_packet)

        if self.pit.node_interest_exists(tlv_data[TLVType.ID], tlv_data[TLVType.NAME_COMPONENT]) is False:
            self.pit.add_interest(tlv_data[TLVType.ID], tlv_data[TLVType.NAME_COMPONENT])
            self.forward_interest(tlv_data)

    def send_data(self, interest_packet, port=-1):
        tlv_data = InterestPacket.decode_tlv(interest_packet)
        if port == -1:
            port = 33000 + int(tlv_data[TLVType.ID].decode())
        data_packet_to_send = self.content_store.get(interest_packet)
        send_socket = self.connect('localhost', port)
        send_socket.send(data_packet_to_send)
        send_socket.close()
        print("Sent Data Packet to " + str(port))

    def connect(self, host, port):
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_socket.connect((host, port))
        print(str(self.network_id) + ": Router connected to " + str(port))
        return send_socket

    def forward_interest(self, tlv_data):
        network_id = int(tlv_data[TLVType.NAME_COMPONENT].decode().split("/")[0].split("network")[1])
        node_id = int(tlv_data[TLVType.NAME_COMPONENT].decode().split("/")[1])
        if network_id != self.network_id:
            next_network_router_id = get_next_node(self.network_id, network_id, self.network_adj_list)
            if next_network_router_id is not None:
                self.send_interest(tlv_data[TLVType.NAME_COMPONENT], 33000 + next_network_router_id, tlv_data[TLVType.SOURCE])
        else:
            self.send_interest(tlv_data[TLVType.NAME_COMPONENT], 33000 + node_id, tlv_data[TLVType.SOURCE])

    def send_interest(self, data, port, source):
        interest_packet_to_send = InterestPacket.encode(data, self.network_id, source)
        send_socket = self.connect('localhost', port)
        send_socket.send(interest_packet_to_send)
        send_socket.close()
        print("Router: Sent Interest Packet to " + str(port))

    def process_data_packet(self, data_packet, tlv_data):
        self.content_store.add_content(data_packet)
        if self.pit.interest_exists(tlv_data[TLVType.NAME_COMPONENT]):
            self.forward_data(data_packet, tlv_data)
            self.pit.remove_interest(tlv_data[TLVType.NAME_COMPONENT].decode())

    def forward_data(self, data_packet, tlv_data):
        for node_id in self.pit.pending_interests.get(tlv_data[TLVType.NAME_COMPONENT].decode()):
            port = (33000 + int(node_id))
            self.send_data(data_packet, port)

    def process_adj_list_packet(self, tlv_data):
        self.network_adj_list = json.loads(tlv_data[TLVType.ADJ_LIST].decode(), object_hook=json_keys_to_int)
        self.distribute_fib()

    def add_node(self):
        new_node_port = 33000 + self.network_id + self.node_id_increment
        new_node_id = self.network_id + self.node_id_increment
        new_node = Node(new_node_port, new_node_id, self.network_id)
        self.nodes.append(new_node)
        create_node_thread = threading.Thread(target=self.run_node, args=(new_node,))
        create_node_thread.start()

        self.node_ids.append(self.network_id + self.node_id_increment)
        self.node_id_increment += 1

        self.node_adj_matrix = self.create_adj_matrix()
        self.distribute_adj_matrix()
        self.distribute_fib()

    def run_node(self, node):
        node.start()

    def distribute_adj_matrix(self):
        for i in range(len(self.node_ids)):
            """""""""
            adj_matrix_json = json.dumps(np.pad(self.node_adj_matrix, (1,0), mode='constant', constant_values=1), cls=NpEncoder)
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_socket.connect(('localhost', 33000 + self.network_id + i + 1))
            send_socket.send(PacketEncoder.encode_adj_list_packet(adj_matrix_json.encode()))
            send_socket.shutdown(socket.SHUT_RDWR)
            send_socket.close()
            """""""""
            self.nodes[i].adj_matrix = np.pad(self.node_adj_matrix, (1,0), mode='constant', constant_values=1)

    def distribute_fib(self):
        time.sleep(1)
        for i in range(len(self.node_ids)):
            """""""""
            fib_entries_json = json.dumps(self.create_fib(self.node_adj_matrix, i).entries, cls=NpEncoder)
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_socket.connect(('localhost', 33000 + self.network_id + i + 1))
            send_socket.send(PacketEncoder.encode_fib_packet(fib_entries_json.encode()))
            send_socket.shutdown(socket.SHUT_RDWR)
            send_socket.close()
            """""""""
            self.nodes[i].fib.entries = self.create_fib(self.node_adj_matrix, i).entries

    def create_adj_matrix(self):
        adj_matrix = np.zeros((len(self.node_ids), len(self.node_ids)), np.uint8)
        for i in range(len(self.node_ids)):
            for j in range(len(self.node_ids) - 1, i - 1, -1):
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
                forwarding_nodes = [node_index + self.network_id + 1 for node_index in forwarding_nodes]
                if len(forwarding_nodes) > 0:
                    fib.add_entry(name_prefix, forwarding_nodes)

        for network_id in self.network_adj_list.keys():
            if network_id != self.network_id:
                name_prefix = "network" + str(network_id) + "/"
                fib.add_entry(name_prefix, [self.network_id, ])

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

    def simulate_movement(self):
        while True:
            time.sleep(random.uniform(5, 10))
            self.node_adj_matrix = self.create_adj_matrix()
            self.distribute_adj_matrix()
            self.distribute_fib()

