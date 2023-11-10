from Network import node
from Network import router
from Network.central_node import CentralNode
from multiprocessing import Process
import time


def create_node(message, port, send, node_id):
    new_node = node.Node(port, node_id)
    if send is True:
        send_socket = new_node.connect('localhost', 30002)
        new_node.send_interest(message, send_socket)
        send_socket.close()


def create_router():
    new_router = router.Router('localhost', 30000)


if __name__ == '__main__':
    print('Test')
    """""""""
    p1 = Process(target=create_node, args=(b'Test/', 30001, True, 1))
    p3 = Process(target=create_node, args=(b'Test/', 30002, False, 2))
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
    central_node = CentralNode(1)
    for i in range(5):
        print("i")
        print(i)
        central_node.add_node()

    #send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #send_socket.connect(('localhost', 33003))
    #central_node.create_adj_matrix()


