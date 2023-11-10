import socket
import threading
import time
import random

from Network.interest_packet import InterestPacket
from Utils.tlv_types import TLVType
from Network.pending_interest_table import PendingInterestTable
from Network.forwarding_information_base import ForwardingInformationBase
from Network.content_store import ContentStore
from Network.data_packet import DataPacket

import json

class Node:
    def __init__(self, port, node_id, network_id):
        self.port = port

        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.network_id = network_id
        self.id = node_id

        self.pit = PendingInterestTable()
        self.fib = ForwardingInformationBase()

        #TODO
        self.content_store = ContentStore()
        for i in range(10):
            self.content_store.add_content("network" + str(self.network_id) + "/" + str(self.id) + "/Test" + str(i), "TestString" + str(i))

        self.adj_matrix = None

        self.init_server()
        self.start()

    def start(self):
        threading.Thread(target=self.run).start()
        threading.Thread(target=self.simulate_interest_request()).start()

    def connect(self, host, port):
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_socket.connect((host, port))
        print("connect")
        return send_socket

    def send_interest(self, data, port):
        print("send")
        interest_packet_to_send = InterestPacket.encode(data, self.id)
        send_socket = self.connect('localhost', port)
        send_socket.send(interest_packet_to_send)
        send_socket.close()

    def send_data(self, name, port):
        content_data = self.content_store.content.get(name)
        data_packet_to_send = DataPacket.encode(name.encode(), content_data.encode())
        send_socket = self.connect('localhost', port)
        send_socket.send(data_packet_to_send)
        send_socket.close()

    def init_server(self):
        """Initialization of the TCP/IP server to receive connections. It binds to the given host and port."""
        print("Initialisation of the Node on port: " + str(self.port) + " on node (" + str(self.id) + ")")
        #self.receive_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print(self.port)
        self.receive_socket.bind(('', self.port))
        self.receive_socket.settimeout(10.0)
        self.receive_socket.listen(1)

    def run(self):
        try:
            print("Router: Wait for incoming connection")

            while True:
                connection, client_address = self.receive_socket.accept()
                data = connection.recv(1024)
                if data:
                    print(data)
                    if len(InterestPacket.decode_tlv(data)) > 0:
                        threading.Thread(target=self.receive_message, args=(data,)).start()
                    else:
                        print(data.decode())

        except Exception as e:
            raise e

    def receive_message(self, data):
        print("received")
        self.process_message(data)

    def process_message(self, data):
        #TODO: works for interest + data packet, move to tlv
        tlv_data = InterestPacket.decode_tlv(data)
        print(tlv_data)
        if TLVType.INTEREST_PACKET in tlv_data:
            print("Interest Packet")
            self.process_interest(tlv_data)
        if TLVType.DATA_PACKET in tlv_data:
            print("Data Packet " + str(self.id))
            self.process_data_packet(tlv_data)
        if len(tlv_data) == 0:
            self.fib.entries = json.loads(data.decode())

    def process_interest(self, tlv_data):
        #TODO: longest prefix search
        if self.content_store.entry_exists(tlv_data[TLVType.NAME_COMPONENT].decode()):
            self.send_data(tlv_data[TLVType.NAME_COMPONENT].decode(),
                           30000 + int(tlv_data[TLVType.ID].decode()))

        if self.pit.node_interest_exists(tlv_data[TLVType.ID], tlv_data[TLVType.NAME_COMPONENT]) is False:
            self.pit.add_interest(tlv_data[TLVType.ID], tlv_data[TLVType.NAME_COMPONENT])
            self.forward_interest(tlv_data)

    def forward_interest(self, tlv_data):
        for node_id in self.fib.get_forwarding_nodes(tlv_data[TLVType.NAME_COMPONENT].decode()):
            #send_socket = self.connect('localhost', 30000 + node_id)
            self.send_interest(tlv_data[TLVType.NAME_COMPONENT], 30000 + node_id)

    def process_data_packet(self, tlv_data):
        self.content_store.add_content(tlv_data[TLVType.NAME_COMPONENT], tlv_data[TLVType.CONTENT])
        if self.pit.interest_exists(tlv_data[TLVType.NAME_COMPONENT]):
            self.forward_data(tlv_data)
            self.pit.remove_interest(tlv_data[TLVType.NAME_COMPONENT].decode())

    def forward_data(self, tlv_data):
        for node_id in self.pit.pending_interests.get(tlv_data[TLVType.NAME_COMPONENT].decode()):
            self.send_data(tlv_data[TLVType.NAME_COMPONENT].decode(), 30000 + int(node_id))

    def is_socket_connected(self, target_port):
        try:
            _, port = self.send_socket.getpeername()
            if target_port == port:
                return True
            else:
                self.send_socket.close()
                self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                return False
        except socket.error:
            return False

    def simulate_interest_request(self):
        while True:
            time.sleep(random.uniform(5, 10))
            print("simulate")
            target_node = random.choice([i for i in range(1, 5)]) + self.network_id
            if target_node != self.id:
                target_data = random.choice([i for i in range(10)])
                name = "network" + str(self.network_id) + "/" + str(target_node) + "/Test" + str(target_data)

                port = 30000 + target_node
                self.send_interest(name.encode(), port)


