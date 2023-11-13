# -*- coding: utf-8 -*-
"""
Created on Sat Nov 11 12:00:41 2023

@author: rombo
"""
import random
import socket
import pandas as pd
import time
import pickle
import threading
import os
import cv2
HEADERSIZE=10

class sensor:
    def __init__(self,sens_id,host,port):
        self.id=sens_id
        self.receive_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host=host
        self.port=port
        self.storage=[]
        #To stop the Threads corresponding to a sensor you put it to True
        self.stop=False
        #Send their data to the connected node every x seconds
        self.frequency_send=20
        #Generate one new object every x seconds
        self.frequency_gen=9
        self.maxstorage=10

#Generate function for random float values between 0 and 1
    """
    def generate(self):
        while not self.stop:
            data=random.uniform(0,1)
            if len(self.storage)>self.maxstorage-1:
                self.storage.pop(0)
            self.storage.append(data)
            time.sleep(self.frequency_gen)
    """   
#Generate function for random captcha folder     
    def generate(self):
        cap=os.listdir("C://Users/rombo/Desktop/Trinity/Cours/Scalable Computing/Project 3/Captcha")
        while not self.stop:
            filename=random.choice(cap)
            data=cv2.imread(os.path.join("C://Users/rombo/Desktop/Trinity/Cours/Scalable Computing/Project 3/Captcha", filename))
            self.receive(data)
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
    
    def run(self):
        try:
            print("Server on")

            while not self.stop:
                connection, client_address = self.receive_socket.accept()
                threading.Thread(target=self.handle,args=(connection,client_address)).start()
        
        except Exception as e:
            raise e
    
    def handle(self,connection,client_address):
                print("receiving")
                data = connection.recv(200000)
                n=int(data[:HEADERSIZE])
                decoded=pickle.loads(data[HEADERSIZE:])
                self.receive(decoded)
                i=1
                while i<n:
                    try:    
                        data = connection.recv(200000)
                        decoded=pickle.loads(data[HEADERSIZE:])
                        self.receive(decoded)
                    except:
                        print("Error no data received")
                    i+=1
                connection.close()
    
    #Designed to remove the oldest object in the storage if max storage capacity is reached before adding new object
    def receive(self,obj):
        if len(self.storage)>self.maxstorage-1:
            self.storage.pop(0)
        self.storage.append(obj)
    
    #Function used to send data to the node to which the sensor is connected
    def send_data(self):
        n=len(self.storage)
        print(f"sending from sensor {self.id}")
        for i in range(n): 
            #First part of the message is a header with the number of objects that are going to be sent, the rest is one object
            msg=bytes(f'{n:<{HEADERSIZE}}',"utf-8")+pickle.dumps(self.storage.pop(0))
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
        
            