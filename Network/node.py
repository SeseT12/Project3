import socket
import threading
from Network.interest_packet import InterestPacket


class Node:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.id = 1

        self.init_server()
        threading.Thread(target=self.run).start()

    def connect(self, host, port):
        self.send_socket.connect((host, port))
        print("connected")

    def send_interest(self, data):
        interest_packet_to_send = InterestPacket.encode(data, self.id)
        print(interest_packet_to_send)
        self.send_socket.send(interest_packet_to_send)

    def init_server(self):
        """Initialization of the TCP/IP server to receive connections. It binds to the given host and port."""
        print("Initialisation of the Node on port: " + str(self.port) + " on node (" + str(self.id) + ")")
        self.receive_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receive_socket.bind(('', self.port))
        self.receive_socket.settimeout(10.0)
        self.receive_socket.listen(1)

    def run(self):
        try:
            print("Node: Wait for incoming connection")
            while True:
                connection, client_address = self.receive_socket.accept()
                data = connection.recv(1024)
                print("Node: received")
                if not data: break
                print("Node Data: " + repr(data))

        except Exception as e:
            raise e


