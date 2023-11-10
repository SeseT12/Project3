from node import Node
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from Utils.tlv_types import TLVType
from Utils import tlv
from key_packet import KeyPacket
from data_packet import DataPacket


class KeyServer(Node):
    def __init__(self, port, id):
        super(KeyServer, self).__init__(port, id)
        self.keyserver = {}

    def add_network(self, name, key):
        self.keyserver[name] = key
    
    def get_key(self, name):
        if name in self.keyserver:
            return self.keyserver[name]
        return "No server found"

    def run(self):
        try:
            print("Node: Wait for incoming connection")
            while True:
                connection, client_address = self.receive_socket.accept()
                data = connection.recv(1024)
                data = KeyPacket.decode_tlv(data)
                if TLVType.KEY_PACKET in data:
                    self.add_network(data[TLVType.NAME], data[TLVType.CONTENT])

                elif TLVType.KEY_REQUEST_PACKET in data:
                    name = data[TLVType.NAME]
                    self.send_key(name, connection)


        except Exception as e:
            raise e

    def send_ack(self, send_socket):
        ACK_message = b'ACK'
        signed_message = self.sign_message(ACK_message)
        ACK_packet = DataPacket.encode("Keyserver", ACK_message + signed_message) #What is name here?
        send_socket.send(ACK_packet)
        send_socket.close()

    def send_key(self, name, send_socket):
        key = self.get_key(name)
        key_signature = self.sign_message(key)
        key_packet = KeyPacket.encode_key(name, key + key_signature)
        send_socket.send(key_packet)
        send_socket.close()


  

