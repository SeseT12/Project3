# Contributor(s): montangr
import random
import socket
import time
import threading
import os
import string
from Network.data_packet import DataPacket
import json
from Utils.Npencoder import NpEncoder
from Utils.tlv_types import TLVType
import numpy as np
import random

typelist=["float"]


def random_name(network_id, device_id, data_type, sensor_id):
    index = random.choice([i for i in range(10)])
    name =  "network" + str(network_id) + "/" + str(device_id) + "/" + data_type + "/" + str(sensor_id) + "/" + str(index)
    return name

def generate_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for i in range(length))
    return random_string


class sensor:
    def __init__(self,sens_id,sens_type,host, network_id, device_id, sensor_id):
        self.id=sens_id
        self.type=sens_type
        self.receive_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host=host
        self.network_id = network_id
        self.device_id = device_id
        self.sensor_id = sensor_id
        self.storage=[]
        #To stop the Threads corresponding to a sensor you put it to True
        self.stop=False
        #Send their data to the connected node every x seconds
        self.frequency_send=5
        #Generate one new object every x seconds
        self.frequency_gen=3
        self.maxstorage=10

#Generate function    
    def generate(self):
        # while True:
        if self.type == "float":
            data = random.uniform(0, 1)
            data_json = json.dumps(data)
            self.receive(data_json)
        elif self.type == "image":
            random_pixels = np.random.randint(0, 256, (4, 4, 3), dtype=np.uint8)
            data_json = json.dumps(random_pixels, cls=NpEncoder)
            self.receive(data_json)
        elif self.type == "integer":
            data = random.randint(0, 10)
            data_json = json.dumps(data)
            self.receive(data_json)
        elif self.type == "string":
            j = random.randint(1, 10)
            data = generate_string(j)
            self.receive(data)
        elif self.type == "timestamp":
            j = random.uniform(0, 10)
            t = time.time()
            data_json = json.dumps((j, t))
            self.receive(data_json)
        elif self.type == "dic":
            j = random.uniform(0, 10)
            t = time.time()
            dic = {"time": t, "value": j}
            data_json = json.dumps(dic)
            self.receive(data_json)
        time.sleep(3)
                
                

    def connect(self,host,port):
        self.send_socket.connect((host, port))
        #print(f"{self.id} connected to {host}")
    
    #Designed to remove the oldest object in the storage if max storage capacity is reached before adding new object
    def receive(self,obj):
        if len(self.storage)>self.maxstorage-1:
            self.storage.pop(0)
        self.storage.append(obj)
    
    #Function used to send data to the node to which the sensor is connected
    def send_data(self):
        if len(self.storage) > 0:
            #print(f"sending from sensor {self.id}")
                #First part of the message is a header with the number of objects that are going to be sent, the rest is one object
            obj=self.storage.pop(0)
            name=random_name(self.network_id, self.device_id, self.type, self.sensor_id)
            packet=DataPacket.encode(name.encode(),self.network_id, self.device_id, obj.encode())
            msg=packet
            self.send_socket.send(msg)
            #close the sending socket and create a new one for the future operations
            self.send_socket.close()
            self.send_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    #Main function which basically starts a sensor and make him automatically generate and send data to a node 
    def transmit(self,host,port):
        # threading.Thread(target=self.generate).start()
        while not self.stop:
            self.generate()
            #transmission frequency of node
            time.sleep(self.frequency_send)
            self.connect(host,port)
            #time necessary to let the connection properly happen
            time.sleep(0.5)
            self.send_data()
    
    def start(self,host,port):
        threading.Thread(target=self.transmit,args=(host,port)).start()

    @staticmethod
    def create_sensors(number,host,port, network_id, device_id):
        sens_type=random.choice(typelist)
        for i in range(number):
            new_sensor=sensor(i+1,sens_type,'', network_id, device_id, i+1)
            new_sensor.start(host,port)
            time.sleep(0.7)
    

            
