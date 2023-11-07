import socket
import threading
import _thread
from Network.pending_interest_table import PendingInterestTable
from Utils.tlv_types import TLVType
from Network.interest_packet import InterestPacket

class Router:
    nodes_ports = [30002]
    nodes_hosts = ["localhost"]

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.pit = PendingInterestTable()

        self.id = 2

        self.init_server()
        threading.Thread(target=self.run).start()

    def init_server(self):
        """Initialization of the TCP/IP server to receive connections. It binds to the given host and port."""
        print("Initialisation of the Router on port: " + str(self.port) + " on node (" + str(self.id) + ")")
        self.receive_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receive_socket.bind(('', self.port))
        self.receive_socket.settimeout(10.0)
        self.receive_socket.listen(1)

    def receive_message(self, receive_socket):
        data = receive_socket.recv(1024)
        print("received")
        if data:
            print("Data: " + repr(data))
            self.process_message(data)
            """""""""
            for i, node_port in enumerate(self.nodes_ports):
                print(node_port)
                print(self.nodes_hosts[i])
                self.connect(self.nodes_hosts[i], node_port)
                self.send_message(b'FromRouter')
            """""""""

    def run(self):
        try:
            print("Router: Wait for incoming connection")
            while True:
                connection, client_address = self.receive_socket.accept()
                threading.Thread(target=self.receive_message, args=(connection,)).start()

        except Exception as e:
            raise e

    def connect(self, host, port):
        self.send_socket.connect((host, port))
        print("connected")

    def send_message(self, message):
        self.send_socket.send(message)

    def process_message(self, data):
        tlv_data = InterestPacket.decode_tlv(data)
        if TLVType.INTEREST_PACKET in tlv_data:
            print("Interest Packet")
            self.pit.add_interest(tlv_data[TLVType.ID], tlv_data[TLVType.NAME_COMPONENT])
        else:
            print("Data Packet")
