# -*- coding: utf-8 -*-
"""
Created on Wed Nov 15 10:21:10 2023

@author: rombo
"""

import random
import socket
import time
import threading
import os
import cv2
import string
from data_packet import DataPacket
import json
from Npencoder import NpEncoder
from tlv_types import TLVType

def random_name(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for i in range(length))
    return random_string

class sensor:
    def __init__(self,sens_id,sens_type,host,port):
        self.id=sens_id
        self.type=sens_type
        self.receive_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host=host
        self.port=port
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
        match self.type:
            case "float":
                while not self.stop:
                    data=random.uniform(0,1)
                    data_json=json.dumps(data)
                    self.receive(data_json)
                    time.sleep(self.frequency_gen)
            case "image":
                cap=os.listdir("C://Users/rombo/Desktop/Trinity/Cours/Scalable Computing/Project 3/Captcha")
                while not self.stop:
                    filename=random.choice(cap)
                    data=cv2.imread(os.path.join("C://Users/rombo/Desktop/Trinity/Cours/Scalable Computing/Project 3/Captcha", filename))
                    data_json=json.dumps(data,cls=NpEncoder)
                    self.receive(data_json)
                    time.sleep(self.frequency_gen)
            case "integer":
                while not self.stop:
                    data=random.randint(0,10)
                    data_json=json.dumps(data)
                    self.receive(data_json)
                    time.sleep(self.frequency_gen)
            case "string":
                while not self.stop:
                    j=random.randint(1,10)
                    data=random_name(j)
                    self.receive(data)
                    time.sleep(self.frequency_gen)
            case "timestamp":
                while not self.stop:
                    j=random.uniform(0,10)
                    t=time.time()
                    data_json=json.dumps((j,t))
                    self.receive(data_json)
                    time.sleep(self.frequency_gen)
            case "dic":
                while not self.stop:
                    j=random.uniform(0,10)
                    t=time.time()
                    dic={"time":t,"value":j}
                    data_json=json.dumps(dic)
                    self.receive(data_json)
                    time.sleep(self.frequency_gen)
                
                

    def connect(self,host,port):
        self.send_socket.connect((host, port))
        print(f"{self.id} connected to {host}")
        
    def init_server(self):
        self.receive_socket.bind((self.host, self.port))
        self.receive_socket.settimeout(30)
        self.receive_socket.listen(8)
        
    def disconnect(self):
        self.receive_socket.close()
        self.send_socket.close()
    
    def handle(self,connection,client_address):
                print("receiving")
                try:
                    data = connection.recv(200000)
                    packet=data
                    decoded=DataPacket.decode_tlv(packet)
                    self.receive(decoded[TLVType.CONTENT])    

                except:
                        print("Error no data received")
                connection.close()
    
    def run(self):
        try:
            print("Server on")

            while not self.stop:
                connection, client_address = self.receive_socket.accept()
                threading.Thread(target=self.handle,args=(connection,client_address)).start()
        
        except Exception as e:
            raise e
    
    def run_server(self):
        threading.Thread(target=self.run).start()
    
    #Designed to remove the oldest object in the storage if max storage capacity is reached before adding new object
    def receive(self,obj):
        if len(self.storage)>self.maxstorage-1:
            self.storage.pop(0)
        self.storage.append(obj)
    
    #Function used to send data to the node to which the sensor is connected
    def send_data(self):
        print(f"sending from sensor {self.id}")
            #First part of the message is a header with the number of objects that are going to be sent, the rest is one object
        obj=self.storage.pop(0)
        name="crouton"
        #name=random_name(10)
        packet=DataPacket.encode(name.encode(),obj.encode())
        msg=packet
        self.send_socket.send(msg)
        #close the sending socket and create a new one for the future operations
        self.send_socket.close()
        self.send_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    #Main function which basically starts a sensor and make him automatically generate and send data to a node 
    def transmit(self,host,port):
        threading.Thread(target=self.generate).start()
        while not self.stop:
            #transmission frequency of node
            time.sleep(self.frequency_send)
            self.connect(host,port)
            #time necessary to let the connection properly happen
            time.sleep(0.5)
            self.send_data()
    
    def start(self,host,port):
        threading.Thread(target=self.transmit,args=(host,port)).start()
    

            