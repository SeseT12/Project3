import socket
import threading
import time
from Network.interest_packet import InterestPacket
from Network.key_packet import KeyPacket
from Utils.tlv_types import TLVType
from Network.pending_interest_table import PendingInterestTable
from Network.forwarding_information_base import ForwardingInformationBase
from Network.content_store import ContentStore
from Network.data_packet import DataPacket
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

KEY_SERVER_HOST = 'localhost'
KEY_SERVER_PORT = 30000 #fix these values when we have them

class Node:
    def __init__(self, port, node_id):
        self.port = port

        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.id = node_id

        self.pit = PendingInterestTable()
        #TODO
        self.fib = ForwardingInformationBase()
        self.fib.add_entry("Test/", [1])

        #TODO
        self.content_store = ContentStore()
        self.content_store.add_content("Test/", "TestString")

        self.private_key = ec.generate_private_key(
            ec.SECP384R1()
            )
        self.keys = {}
        self.register_key()

        #TODO
        self.connections = {1: 30001, 2: 30002}

        self.init_server()
        threading.Thread(target=self.run).start()

    def connect(self, host, port):
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_socket.connect((host, port))
        return send_socket

    def send_interest(self, data, send_socket):
        print("send")
        interest_packet_to_send = InterestPacket.encode(data, self.id)
        send_socket.send(interest_packet_to_send)
        send_socket.close()

    def send_data(self, name, port):
        content_data = self.content_store.content.get(name)
        content_signature = self.sign_message(content_data)
        data_packet_to_send = DataPacket.encode(name.encode(), content_data.encode(), content_signature)
        send_socket = self.connect('localhost', port)
        send_socket.send(data_packet_to_send)
        send_socket.close()

    def init_server(self):
        """Initialization of the TCP/IP server to receive connections. It binds to the given host and port."""
        print("Initialisation of the Node on port: " + str(self.port) + " on node (" + str(self.id) + ")")
        self.receive_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receive_socket.bind(('', self.port))
        self.receive_socket.settimeout(10.0)
        self.receive_socket.listen(1)

    def run(self):
        try:
            print("Router: Wait for incoming connection")
            connection, client_address = self.receive_socket.accept()
            while True:
                data = connection.recv(1024)
                if data:
                    threading.Thread(target=self.receive_message, args=(data,)).start()

        except Exception as e:
            raise e

    def receive_message(self, data):
        print("received")
        self.process_message(data)

    def process_message(self, data):
        #TODO: works for interest + data packet, move to tlv
        tlv_data = InterestPacket.decode_tlv(data)
        if TLVType.INTEREST_PACKET in tlv_data:
            print("Interest Packet")
            self.process_interest(tlv_data)
        if TLVType.DATA_PACKET in tlv_data:
            print("Data Packet " + str(self.id))
            self.process_data_packet(tlv_data)

    def process_interest(self, tlv_data):
        if self.content_store.entry_exists(tlv_data[TLVType.NAME_COMPONENT].decode()):
            self.send_data(tlv_data[TLVType.NAME_COMPONENT].decode(),
                           self.connections.get(int(tlv_data[TLVType.ID].decode())))

        if self.pit.node_interest_exists(tlv_data[TLVType.ID], tlv_data[TLVType.NAME_COMPONENT]) is False:
            self.pit.add_interest(tlv_data[TLVType.ID], tlv_data[TLVType.NAME_COMPONENT])
            self.forward_interest(tlv_data)

    def forward_interest(self, tlv_data):
        for node_id in self.fib.get_forwarding_nodes(tlv_data[TLVType.NAME_COMPONENT].decode()):
            send_socket = self.connect('localhost', self.connections.get(node_id))
            self.send_interest(tlv_data[TLVType.NAME_COMPONENT], send_socket)

    def process_data_packet(self, tlv_data):
        if self.verify_message(tlv_data[TLVType.CONTENT], tlv_data[TLVType.SIGNATURE], tlv_data[TLVType.NAME_COMPONENT].decode()):
            print("Data packet verified")
            self.content_store.add_content(tlv_data[TLVType.NAME_COMPONENT], tlv_data[TLVType.CONTENT])
            if self.pit.interest_exists(tlv_data[TLVType.NAME_COMPONENT]):
                self.forward_data(tlv_data)
                self.pit.remove_interest(tlv_data[TLVType.NAME_COMPONENT].decode())
        else:
            print("Data packet not verified")

    def forward_data(self, tlv_data):
        for node_id in self.pit.pending_interests.get(tlv_data[TLVType.NAME_COMPONENT].decode()):
            self.send_data(tlv_data[TLVType.NAME_COMPONENT].decode(), self.connections.get(int(node_id)))

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

    def sign_message(self, message):
        sig = self.private_key.sign(
            message,
            ec.ECDSA(hashes.SHA256())
        )
        return sig

    def verify_message(self, message, signature, sender_name):
        if sender_name in self.keys:
            sender_key = self.keys[sender_name]
        else:
            sender_key = self.get_key(sender_name)
        sender_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True

    def verify_first_message(self, message, signature): # this should be for adding keys, so message should be the key
        public_key = serialization.load_pem_public_key(message)
        public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True

    def get_key(self, sender_name):
        # contact keyserver for public key
        signature = self.sign_message(sender_name)
        key_request_packet = KeyPacket.encode_request(str(self.id).encode(), sender_name.encode(), signature)
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
            if self.verify_message(content, signature, "keyserver"):
                public_key = serialization.load_pem_public_key(content)
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
        key_packet = KeyPacket.encode_key(str(self.id).encode(), serialized_public, signature)
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
                public_key = serialization.load_pem_public_key(content)
                self.keys["keyserver"] = public_key
                keyserver_socket.close()
                return "Key registered"
            else:
                keyserver_socket.close()
                return "Invalid signature"

        except Exception as e:
            raise e