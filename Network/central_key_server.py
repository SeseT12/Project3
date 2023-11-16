from Network.node import Node
from Utils.tlv_types import TLVType
from Utils import tlv
from Network.key_packet import KeyPacket
from Network.data_packet import DataPacket
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
import threading


class KeyServer(Node):
    def __init__(self, port, id, network_id):
        super(KeyServer, self).__init__(port, id, network_id)
        self.keyserver = {}
        self.keyserver['keyserver'] = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def add_network(self, name, key):
        self.keyserver[name] = key
    
    def get_key(self, name):
        if name in self.keyserver:
            return self.keyserver[name]
        print("No key found for node ", name)
        #print keys of keyserver
        return "No key found"

    def run(self):
        try:
            print("Keyserver: Wait for incoming connection")
            while True:
                connection, client_address = self.receive_socket.accept()
                data = connection.recv(1024)
                data = KeyPacket.decode_tlv(data)
                if TLVType.KEY_PACKET in data:
                    content = data[TLVType.CONTENT]
                    signature = data[TLVType.SIGNATURE]
                    if self.verify_first_message(content, signature):
                        # public_key = serialization.load_pem_public_key(content)
                        self.add_network(data[TLVType.NAME].decode(), content)
                        print("Added key for node ", data[TLVType.NAME].decode())
                        self.send_key('keyserver', connection)

                elif TLVType.KEY_REQUEST_PACKET in data:
                    name = data[TLVType.NAME].decode()
                    self.send_key(name, connection)
                else:
                    print("Invalid packet")

        except Exception as e:
            raise e

    def send_ack(self, send_socket):
        ACK_message = b'ACK'
        signed_message = self.sign_message(ACK_message)
        ACK_packet = DataPacket.encode(self.network_id, self.id, b'keyserver', ACK_message, signed_message)
        send_socket.send(ACK_packet)
        send_socket.close()

    def send_key(self, name, send_socket):
        key = self.get_key(name)
        if key == "No key found":
            serialized_public = b'NOKEY' # in case no key is found
        else:
            serialized_public = key

        key_signature = self.sign_message(serialized_public)
        key_packet = KeyPacket.encode_key(name.encode() if type(name) is str else name, serialized_public, key_signature)
        send_socket.send(key_packet)
        send_socket.close()

    def register_key(self):
        pass

    def start(self):
        threading.Thread(target=self.run).start()
