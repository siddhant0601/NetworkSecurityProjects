import socket
import time
import sys
import json
import random
import threading
from RSA import encrypt, decrypt

class PKDAClient:
    def __init__(self, address,address2):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect(address)

            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.bind(address2)
            self.client_socket.listen(5)

            self.client_name = "mahansh"

            self.private_key=(578129, 545873)
            self.public_key=(578129, 461873)

            self.pkda_public_key = (857393, 719249)
            self.keyList={}

            self.my_nonce = set()
            self.others_nonce = set()

        except Exception as e:
            print(f"Error initializing client: {e}")
            sys.exit(1)

    def generate_nonce(self, entity):
        nonce = random.randint(1, 10000)
        
        while nonce in self.my_nonce or nonce in self.others_nonce:
            nonce = random.randint(1, 10000)

        if entity == 'mine':
            self.my_nonce.add(nonce)
        elif entity == 'others':
            self.others_nonce.add(nonce)
            
        return nonce

    def construct_message(self, sender):
        timestamp = int(time.time())
        duration = 300

        message_data = {
            'sender' : sender,
            'timestamp': timestamp,
            'duration' : duration,
        }

        return message_data

    def validate_response(self, response):
        print("checking nonce and timestamp")
        if 'error' in response:
            print(f"[.] ERROR FROM SERVER: {response['error']}")
            sys.exit()
        if response.get('nonce2') not in self.my_nonce:
            print("wrong nonce recevied")
            sys.exit()
            
        nonce = response.get('nonce')
        timestamp = response.get('timestamp')

        if nonce in self.my_nonce or nonce in self.others_nonce:
            print(f"[.] INVALIED NONCE {nonce} RECEIVED. NONCE SHOULD BE UNIQUE.")
            sys.exit()
            
        
        current_time = int(time.time())
        if current_time - timestamp > 300: 
            print(f"[.] REQUEST FROM {response.get('sender')} ARRIVED OUTSIDE OF THE TIME DURATION.")
            sys.exit()
            
        return True
    
    def dataThread(self,client_socket):
            try:
                while True:
                    response = self.receive_message(client_socket, 1)
                    myres=response['message'].split()
                    if not response:
                        continue
                    print(f"[.] MESSAGE RECEIVED FROM RANA: {response['message']}")
                    if myres[0]=="GOT":
                        continue
                    self.send_message(client_socket,False,1, message=f"GOT IT : {response['message']}")
                    
                            # Handle the received response here as per your requirements
            except Exception as e:
                pass

    def receive_key(self):
        request_data = self.construct_message(self.client_name)
        request_data['requested_id'] = 'rana'
        # nonce = self.generate_nonce('mine')
        print("[.] 1) REQUESTING KEY OF mahansh")
        self.server_socket.send(json.dumps(request_data).encode())

        response = json.loads(decrypt(json.loads(self.server_socket.recv(2048).decode()), self.pkda_public_key))
        
        # if self.validate_response(response):
        print(f"[.] 2) RECIEVED KEY: {response['message']['public_key']}")

        if "rana" not in self.keyList:
            self.keyList["rana"] = response['message']['public_key']
            print(f"success:key of other user{response['message']['public_key']}")
    def send_message(self, client_socket, createNounce,step,nonce2=None, message=None):
        send_data = self.construct_message(self.client_name)
        nonce=None
        if createNounce:
            nonce = self.generate_nonce('mine')
            print(f"generating nonce {nonce} ")
        if nonce2:
            send_data['nonce2'] = nonce2
        if nonce:
            send_data['nonce1']=nonce
        if message:
            send_data['message'] = message
        print(f'sending msg {send_data}')
        client_socket.send(json.dumps(encrypt(json.dumps(send_data), tuple(self.keyList['rana']))).encode())
       
    
    
    def receive_message(self, client_socket, step):
        response = json.loads(decrypt(json.loads(client_socket.recv(2048).decode()), self.private_key))
        return response

    def exchangeKeysY(self,client_socket):
        self.receive_key()
        self.send_message(client_socket,True, 3)
        response = self.receive_message(client_socket, 6)
        print(f"[.] MESSAGE RECEIVED FROM RANA: {response}")
        self.validate_response(response)
        # validate noucne and time
        self.send_message(client_socket, False,7, nonce2=response['nonce1'])
        print("key exchange success ------------------------------")

    def exchangeKeysN(self,client_socket):
        response = self.receive_message(client_socket,3)
        print(response)
        self.receive_key()
        print(f"[.] MESSAGE RECEIVIED FROM RANA WAS {response}")
        self.send_message(client_socket,True,6, nonce2= response['nonce1'])
        response = self.receive_message(client_socket,7)
        print(f"[.] MESSAGE RECEIVIED FROM RANA WAS  {response}")
        print("key exchange success-----------------------------")
        
    def run(self,init):
        client_socket, other_client_address = self.client_socket.accept()
        print(f"[.] CONNECTION ESTABLISHED WITH {other_client_address}.")
        if init=="I":
            self.exchangeKeysY(client_socket)
        elif init=="R":
            self.exchangeKeysN(client_socket)
        else:
            print("wrond command")
            exit()
        # while(True):
        self.receive_thread = threading.Thread(target=self.dataThread, args=(client_socket,))
        self.receive_thread.daemon = True  # Daemonize the thread
        self.receive_thread.start()
            # msg=input("enter msg to send to rana ")
        send_id=8
        while(True):
            message=input("enter msg to send to rana")
            self.send_message(client_socket,False, send_id, message=message)
            receive_id = send_id + 1
            # response = self.receive_message(client_socket, receive_id)
            # print(f"[.] MESSAGE RECEIVED FROM RANA: {response['message']}")

if __name__ == "__main__":

    address = ("127.0.0.1", 5678)
    address2 = ("127.0.0.1", 5679)
    init=input("are you initiator or responder I / R")
    pkda_client = PKDAClient(address,address2)
    pkda_client.run(init)
