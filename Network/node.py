import socket
import threading
import time
import random
import numpy as np

from Network.interest_packet import InterestPacket
from Network.key_packet import KeyPacket
from Utils.json_keys_to_int import json_keys_to_int
from Utils.tlv_types import TLVType
from Network.pending_interest_table import PendingInterestTable
from Network.forwarding_information_base import ForwardingInformationBase
from Network.content_store import ContentStore
from Network.data_packet import DataPacket
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from Network.sensor import sensor
import Network.sensor

import json
import select
KEY_SERVER_HOST = 'rasp-039.berry.scss.tcd.ie'
KEY_SERVER_PORT = 30500 #fix these values when we have them

class Node:
    def __init__(self, port, node_id, network_id):
        self.port = port

        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.network_id = network_id
        self.id = node_id

        self.private_key = ec.generate_private_key(
            ec.SECP384R1(),
            default_backend()
        )
        self.keys = {}
        self.register_key()
        
        self.pit = PendingInterestTable()
        self.fib = ForwardingInformationBase()

        self.content_store = ContentStore()
        #self.populate_content_store(10)

        self.adj_matrix = None


        self.init_server()
        #self.start()
        
        #Initialize the sensors for this node
        #sensor.create_sensors(8,'localhost', self.port, self.network_id, self.id)
        threading.Thread(target=sensor.create_sensors, args=(8, 'localhost', self.port, self.network_id, self.id)).start()
        
    def start(self):
        threading.Thread(target=self.run).start()
        threading.Thread(target=self.simulate_interest_request()).start()

    def connect(self, host, port):
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_socket.connect((host, port))
        print(str(self.id) + ": Connected to " + str(port))
        return send_socket

    def send_interest(self, data, port, source):
        print("Send interest from " + str(self.id) + "to " + str(port))
        interest_packet_to_send = InterestPacket.encode(data, self.id, source)
        if self.adj_matrix is not None and self.adj_matrix[self.id - self.network_id][port - self.network_id - 30000] == 1:
            send_socket = self.connect('localhost', port)
            with threading.Lock():
                send_socket.send(interest_packet_to_send)
            send_socket.shutdown(socket.SHUT_RD)
            send_socket.close()
            print(str(self.id) + ": Sent Interest Packet to " + str(port))
        else:
            print("Not Connected")

    def send_data(self, interest_packet, port=-1):
        if self.adj_matrix is not None and self.adj_matrix[self.id - self.network_id][
            port - self.network_id - 30000] == 1:
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

        else:
            print("Not Connected")

    def init_server(self):
        """Initialization of the TCP/IP server to receive connections. It binds to the given host and port."""
        print("Initialisation of the Node on port: " + str(self.port) + " on node (" + str(self.id) + ")")
        self.receive_socket.bind(('', self.port))
        self.receive_socket.settimeout(10.0)
        self.receive_socket.listen(5)

    def run(self):
        try:
            print("Node: Wait for incoming connection")

            interval_seconds = 5
            last_run_time = time.time()

            while True:
                    readable, _, _ = select.select([self.receive_socket], [], [], 10.0)

                    if self.receive_socket in readable:
                        connection, client_address = self.receive_socket.accept()
                        message_process_thread = threading.Thread(target=self.receive_message, args=(connection,))
                        message_process_thread.start()
                        #message_process_thread.join()

                    if time.time() - last_run_time >= interval_seconds:
                        self.renew_pending_interests()
                        print("RENEW PIT")
                        last_run_time = time.time()

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
            #print(str(self.id) + ": Received Interest Packet from " + tlv_data[TLVType.ID].decode())
        if TLVType.DATA_PACKET in tlv_data:
            self.process_data_packet(data, tlv_data)
            #print(str(self.id) + ": Received Data Packet")
        if TLVType.FIB in tlv_data:
            self.fib.entries = json.loads(tlv_data[TLVType.FIB].decode(), object_hook=json_keys_to_int)
        if TLVType.ADJ_LIST in tlv_data:
            self.adj_matrix = np.asarray(json.loads(tlv_data[TLVType.ADJ_LIST].decode()))

    def process_interest(self, interest_packet):
        tlv_data = InterestPacket.decode_tlv(interest_packet)
        if self.content_store.entry_exists(interest_packet): #tlv_data[TLVType.NAME_COMPONENT].decode()):
            port = (30000 + int(tlv_data[TLVType.ID].decode()))
            self.send_data(interest_packet, port)

        elif self.pit.node_interest_exists(tlv_data[TLVType.ID], tlv_data[TLVType.NAME_COMPONENT]) is False:
            self.pit.add_interest(tlv_data[TLVType.ID], tlv_data[TLVType.NAME_COMPONENT])
            self.forward_interest(tlv_data)

    def forward_interest(self, tlv_data):
        for node_id in self.fib.get_forwarding_nodes(tlv_data[TLVType.NAME_COMPONENT].decode()):
            if self.pit.node_interest_exists(str(node_id).encode(), tlv_data[TLVType.NAME_COMPONENT]) is False:
                self.send_interest(tlv_data[TLVType.NAME_COMPONENT], 30000 + node_id, tlv_data[TLVType.SOURCE])
                time.sleep(1)

    def process_data_packet(self, data_packet, tlv_data):
        if self.verify_message(tlv_data[TLVType.CONTENT], tlv_data[TLVType.SIGNATURE],
                               tlv_data[TLVType.NAME_COMPONENT].decode(), tlv_data[TLVType.ID].decode()):
            self.content_store.add_content(data_packet)
            if self.pit.interest_exists(tlv_data[TLVType.NAME_COMPONENT]):
                self.forward_data(data_packet, tlv_data)
                self.pit.remove_interest(tlv_data[TLVType.NAME_COMPONENT].decode())
        else:
            print("Data packet not verified")
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

    def populate_content_store(self, n_entries):
        for i in range(n_entries):
            name = "network" + str(self.network_id) + "/" + str(self.id) + "/Test" + str(i)
            data = "TestString" + str(i)
            sig = self.sign_message(data)
            data_packet = DataPacket.encode(name.encode(), self.network_id, self.id, data.encode(), sig)
            self.content_store.add_content(data_packet)

    def simulate_interest_request(self):
        time.sleep(5)
        print("simulate interest: " + str(self.network_id))
        while True:
            time.sleep(random.uniform(5, 10))
            #target_node = random.choice([i for i in range(1, 5)]) + 31#self.network_id
            #network_id = self.network_id
            if len(self.fib.entries) > 0:
                name = random.choice(self.fib.entries)[0]

                if len(name.split("/")) < 3:
                    network_id = int(name.split("/")[0].split("network")[1])
                    name += str(random.choice([i for i in range(1, 5)]) + network_id) + "/"

                data_index = random.choice([i for i in range(10)])
                data_type = random.choice(Network.sensor.typelist)
                sensor_id = random.choice([i for i in range(8)]) + 1
                name += data_type + "/" + str(sensor_id) + "/" + str(data_index)
                print("Node " + str(self.id) + " expressed Interest in: " + name)
                for node_id in self.fib.get_forwarding_nodes(name):
                    print(self.fib.get_forwarding_nodes(name))
                    self.send_interest(name.encode(), 30000 + node_id, str(self.network_id) + "/" + str(self.id))
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
    def sign_message(self, message):
        if type(message) is str:
            message = message.encode()
        try:
            sig = self.private_key.sign(
                message,
                ec.ECDSA(hashes.SHA256())
            )
            return sig
        except Exception as e:
            print(e)
            print("Broken Message ", message)
            print("Broken Message Type ", type(message))
            return None

    def verify_message(self, message, signature, sender_name, id):
        if signature == b'NOSIG':
            return True
        if id in self.keys:
            sender_key = self.keys[id]
            if sender_key == "No key found":
                sender_key = self.get_key(id)
                self.keys[id] = sender_key
        else:
            sender_key = self.get_key(id)
            if sender_key == "No key found":
                for i in range(3):
                    time.sleep(0.2)
                    sender_key = self.get_key(id)
                    if sender_key != "No key found":
                        break
                if sender_key == "No key found":
                    print("No key found")
                    return False
        if type(sender_key) is bytes:
            sender_public_key = serialization.load_pem_public_key(sender_key, default_backend())
        try:
            sender_public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
            # print("Message verified")
            # print("Message: ", message)
            # print("Signature: ", signature)
            # print("Sender: ", sender_name)
            # print("ID: ", id)
            # print("Sender key: ", sender_key)
        except:
            print("Invalid signature")
            print("Message: ", message)
            print("Signature: ", signature)
            print("Sender: ", sender_name)
            print("ID: ", id)
            print("Own ID: {}/{}".format(self.network_id, self.id))
            print("Sender key: ", sender_key)
            return False
        return True

    def verify_first_message(self, message, signature): # this should be for adding keys, so message should be the key
        if signature == b'NOSIG': # for sensors
            return True
        public_key = serialization.load_pem_public_key(message, default_backend())
        public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True

    def get_key(self, sender_name):
        # contact keyserver for public key
        signature = self.sign_message(sender_name)
        network_name_id = str(self.network_id) + "/" + str(self.id)
        key_request_packet = KeyPacket.encode_request(sender_name.encode(), sender_name.encode(), signature)
        try:
            keyserver_socket = self.connect(KEY_SERVER_HOST, KEY_SERVER_PORT)
            keyserver_socket.send(key_request_packet)
            time.sleep(1) # can reduce this, also need to have a fail case
            reply = keyserver_socket.recv(1024)
            if not reply:
                keyserver_socket.close()
                return "No reply from keyserver"
            data = KeyPacket.decode_tlv(reply)
            content = data[TLVType.CONTENT]
            signature = data[TLVType.SIGNATURE]
            if self.verify_message(content, signature, "keyserver", "keyserver"):
                if content == b'NOKEY':
                    keyserver_socket.close()
                    return "No key found"
                public_key = content
                self.keys[sender_name] = public_key
                keyserver_socket.close()
                return content
            else:
                keyserver_socket.close()
                return "Invalid signature"

        except Exception as e:
            raise e

    def register_key(self):
        serialized_public = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        signature = self.sign_message(serialized_public)
        network_name_id = str(self.network_id) + "/" + str(self.id)
        key_packet = KeyPacket.encode_key(network_name_id.encode(), serialized_public, signature)
        try:
            keyserver_socket = self.connect(KEY_SERVER_HOST, KEY_SERVER_PORT)
            keyserver_socket.send(key_packet)
            print("Node {} sent key to keyserver".format(self.id))
            reply = keyserver_socket.recv(1024)
            if not reply:
                keyserver_socket.close()
                return "No reply from keyserver"
            data = DataPacket.decode_tlv(reply)
            content = data[TLVType.CONTENT]
            signature = data[TLVType.SIGNATURE]
            if self.verify_first_message(content, signature):
                # public_key = serialization.load_pem_public_key(content)
                public_key = content
                self.keys["keyserver"] = public_key
                keyserver_socket.close()
                return "Key registered"
            else:
                keyserver_socket.close()
                return "Invalid signature"

        except Exception as e:
            raise e



    def renew_pending_interests(self):
        for (node_id, name) in self.pit.get_old_pending_interests():
            if name in self.content_store.keys:
                self.send_data(name, node_id + 30000)

