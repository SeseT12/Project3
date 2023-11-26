# Contributor(s): cobreath
import os.path

from Network import node
from Network import router
from Network.central_node import CentralNode
from Network.global_node import GlobalNode
from Network.forwarding_information_base import ForwardingInformationBase
from multiprocessing import Process
from Utils.shortest_path import get_next_node
import time
import numpy as np

from Network.central_key_server import KeyServer
from Network.interest_packet import InterestPacket
from Utils.tlv import decode_tlv


if __name__ == '__main__':
    print('Test')
    # keyserver = KeyServer(30500, 0, 10)
    """""""""
    p1 = Process(target=create_node, args=(b'Test/', 33001, True, 1))
    p3 = Process(target=create_node, args=(b'Test/', 33002, False, 2))
    #p2 = Process(target=create_router)
    #p2.start()
    p3.start()
    #p2.join()
    time.sleep(1)
    p1.start()
    #time.sleep(1)
    #p1.join()
    #p3.join()
    """""""""
    """""""""
    test_ip = InterestPacket.encode(b"Test")
    print(test_ip.hex())
    print(decode_tlv(test_ip))
    print(InterestPacket.decode_tlv(test_ip))
    """""""""
    #central_node = CentralNode(1)
    #for i in range(5):
    #    central_node.add_node()
    #"""""""""""
    global_node = GlobalNode()
    for i in range(5):
        global_node.add_network()
        time.sleep(1)
    #"""""""""""

    #central_node = CentralNode(1)
    #test = np.array([[0, 1, 1, 0, 0], [1, 0, 1, 0, 1], [1, 1, 0, 1, 1], [0, 0, 1, 0, 0], [0, 1, 1, 0, 0]])
    #print(test)
    #for i in range(5):
    #    print(central_node.create_fib(test, i).entries)

    #send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #send_socket.connect(('localhost', 33003))
    #central_node.create_adj_matrix()


