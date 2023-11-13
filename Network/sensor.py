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
        #Include a parameter to connect the sensor to a certain node ?
        self.id=sens_id
        self.receive_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host=host
        self.port=port
        #remplacer le storage par pandas pour d'autres data ?
        #self.storage=pd.
        #self.storage dico avec nom data généré arbitrairement et valeur ?
        self.storage=[]
        self.stop=False
        self.frequency_send=20
        self.frequency_gen=9
        self.maxstorage=10

    """
    def generate(self):
        while not self.stop:
            data=random.uniform(0,1)
            if len(self.storage)>self.maxstorage-1:
                self.storage.pop(0)
            self.storage.append(data)
            time.sleep(self.frequency_gen)
    """        
    def generate(self):
        cap=os.listdir("C://Users/rombo/Desktop/Trinity/Cours/Scalable Computing/Project 3/Captcha")
        while not self.stop:
            filename=random.choice(cap)
            data=cv2.imread(os.path.join("C://Users/rombo/Desktop/Trinity/Cours/Scalable Computing/Project 3/Captcha", filename))
            if len(self.storage)>self.maxstorage-1:
                self.storage.pop(0)
            self.storage.append(data)
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
    
    def receive(self,obj):
        if len(self.storage)>self.maxstorage-1:
            self.storage.pop(0)
        self.storage.append(obj)
    
    def send_data(self):
        n=len(self.storage)
        print(f"sending from sensor {self.id}")
        for i in range(n): 
            msg=bytes(f'{n:<{HEADERSIZE}}',"utf-8")+pickle.dumps(self.storage.pop(0))
            self.send_socket.send(msg)
        self.send_socket.close()
        self.send_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def transmit(self,host,port):
        threading.Thread(target=self.generate).start()
        while not self.stop:
            #transmission frequency of node
            time.sleep(self.frequency_send)
            self.connect(host,port)
            #time necessary to let the connection properly happen
            time.sleep(0.5)
            self.send_data()
        
            