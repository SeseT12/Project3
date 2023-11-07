from Network import node
from Network import router
from multiprocessing import Process
import time
from Network.interest_packet import InterestPacket
from Utils.tlv import decode_tlv


def create_node(name, message, port, send):
    new_node = node.Node(name, port)
    if send is True:
        new_node.connect('localhost', 30000)
        new_node.send_interest(message)


def create_router():
    new_router = router.Router('localhost', 30000)


if __name__ == '__main__':
    print('Test')
    #"""""""""
    p1 = Process(target=create_node, args=("test_node", b'Test1', 30001, True))
    p3 = Process(target=create_node, args=("test_node_2", b'Test2', 30002, False))
    p2 = Process(target=create_router)
    p2.start()
    p3.start()
    #p2.join()
    time.sleep(1)
    p1.start()
    #time.sleep(1)
    #p1.join()
    #p3.join()
    
    test_ip = InterestPacket.encode(b"Test")
    print(test_ip.hex())
    print(decode_tlv(test_ip))
    print(InterestPacket.decode_tlv(test_ip))
    


