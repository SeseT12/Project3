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
from Network.sensor import sensor

import json
import select

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
            name = "network" + str(self.network_id) + "/" + str(self.id) + "/Test" + str(i)
            data = "TestString" + str(i)
            data_packet = DataPacket.encode(name.encode(), data.encode())
            self.content_store.add_content(data_packet)

        self.adj_matrix = None

        self.init_server()
        self.start()
        
        #Initialize the sensors for this node
        #sensor.create_sensors(8,'localhost',self.port)
        
    def start(self):
        threading.Thread(target=self.run).start()
        threading.Thread(target=self.simulate_interest_request()).start()

    def connect(self, host, port):
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_socket.connect((host, port))
        print(str(self.id) + ": Connected to " + str(port))
        return send_socket

    def send_interest(self, data, port):
        interest_packet_to_send = InterestPacket.encode(data, self.id)
        send_socket = self.connect('localhost', port)
        with threading.Lock():
            send_socket.send(interest_packet_to_send)
        send_socket.shutdown(socket.SHUT_RD)
        send_socket.close()
        print(str(self.id) + ": Sent Interest Packet to " + str(port))

    def send_data(self, interest_packet, port=-1):
        tlv_data = InterestPacket.decode_tlv(interest_packet)
        if port == -1:
            port = 30000 + int(tlv_data[TLVType.ID].decode())
        data_packet_to_send = self.content_store.get(interest_packet)
        send_socket = self.connect('localhost', port)
        with threading.Lock():
            send_socket.send(data_packet_to_send)
        send_socket.shutdown(socket.SHUT_RD)
        send_socket.close()
        print(str(self.id) + ": Sent Data Packet to " + str(port))

    def init_server(self):
        """Initialization of the TCP/IP server to receive connections. It binds to the given host and port."""
        print("Initialisation of the Node on port: " + str(self.port) + " on node (" + str(self.id) + ")")
        self.receive_socket.bind(('', self.port))
        self.receive_socket.settimeout(10.0)
        self.receive_socket.listen(5)

    def run(self):
        try:
            print("Node: Wait for incoming connection")

            while True:
                readable, _, _ = select.select([self.receive_socket], [], [], 10.0)

                if self.receive_socket in readable:
                    connection, client_address = self.receive_socket.accept()
                    message_process_thread = threading.Thread(target=self.receive_message, args=(connection,))
                    message_process_thread.start()
                    #message_process_thread.join()

        except Exception as e:
            raise e

    def receive_message(self, connection):
        with threading.Lock():
            while True:
                data = connection.recv(1024)
                if data:
                    self.process_message(data)
                else:
                    break

    def process_message(self, data):
        #TODO: works for interest + data packet, move to tlv
        tlv_data = InterestPacket.decode_tlv(data)
        if TLVType.INTEREST_PACKET in tlv_data:
            self.process_interest(data)
            print(str(self.id) + ": Received Interest Packet from " + tlv_data[TLVType.ID].decode())
        if TLVType.DATA_PACKET in tlv_data:
            self.process_data_packet(data, tlv_data)
            print(str(self.id) + ": Received Data Packet")
        if len(tlv_data) == 0:
            #print("Received FIB")
            self.fib.entries = json.loads(data.decode())

    def process_interest(self, interest_packet):
        tlv_data = InterestPacket.decode_tlv(interest_packet)
        if self.content_store.entry_exists(interest_packet): #tlv_data[TLVType.NAME_COMPONENT].decode()):
            self.send_data(interest_packet)

        elif self.pit.node_interest_exists(tlv_data[TLVType.ID], tlv_data[TLVType.NAME_COMPONENT]) is False:
            self.pit.add_interest(tlv_data[TLVType.ID], tlv_data[TLVType.NAME_COMPONENT])
            self.forward_interest(tlv_data)

    def forward_interest(self, tlv_data):
        for node_id in self.fib.get_forwarding_nodes(tlv_data[TLVType.NAME_COMPONENT].decode()):
            if self.pit.node_interest_exists(str(node_id).encode(), tlv_data[TLVType.NAME_COMPONENT]) is False:
                self.send_interest(tlv_data[TLVType.NAME_COMPONENT], 30000 + node_id)
                time.sleep(1)

    def process_data_packet(self, data_packet, tlv_data):
        self.content_store.add_content(data_packet)
        if self.pit.interest_exists(tlv_data[TLVType.NAME_COMPONENT]):
            self.forward_data(data_packet, tlv_data)
            self.pit.remove_interest(tlv_data[TLVType.NAME_COMPONENT].decode())

    def forward_data(self, data_packet, tlv_data):
        for node_id in self.pit.pending_interests.get(tlv_data[TLVType.NAME_COMPONENT].decode()):
            port = (30000 + int(node_id))
            self.send_data(data_packet, port)

    def is_socket_connected(self, target_port):
        try:
            _, port = self.send_socket.getpeername()
            if target_port == port:
                return True
            else:
                #self.send_socket.close()
                print(str(self.id) + ": Close")
                self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                return False
        except socket.error:
            return False

    def simulate_interest_request(self):
        time.sleep(5)
        print("simulate interest: " + str(self.network_id))
        while True:
            time.sleep(random.uniform(5, 10))
            #target_node = random.choice([i for i in range(1, 5)]) + 31#self.network_id
            #network_id = self.network_id
            print(self.fib.entries)
            name = random.choice(self.fib.entries)[0]

            if len(name.split("/")) < 3:
                network_id = int(name.split("/")[0].split("network")[1])
                name += str(random.choice([i for i in range(1, 5)]) + network_id) + "/"

            target_data = random.choice([i for i in range(10)])
            name += "Test" + str(target_data)
            print("Node " + str(self.id) + " expressed Interest in: " + name)
            for node_id in self.fib.get_forwarding_nodes(name):
                print(self.fib.get_forwarding_nodes(name))
                self.send_interest(name.encode(), 30000 + node_id)
            #port = 30000 + int((name.split("/")[0] + "/")[0])
            """""""""""
            target_data = random.choice([i for i in range(10)])
            name = "network" + str(network_id) + "/" + str(target_node) + "/Test" + str(target_data)

            port = 30000 + target_node
            #self.send_interest(name.encode(), port)
            port = 30000 + int(self.fib.get_forwarding_nodes(name.split("/")[0] + "/")[0])
            print("send simulate")
            self.send_interest(name.encode(), port)
            """""""""""

