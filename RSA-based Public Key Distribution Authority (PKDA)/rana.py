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
            self.client_socket.connect(address2)



            self.client_name = "rana"
            
            self.private_key=(732857, 695627)
            self.public_key=(732857, 91235)

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
    
    def receive_key(self):
        request_data = self.construct_message(self.client_name)
        request_data['requested_id'] = 'mahansh'
        print("[.] 4) REQUESTING KEY OF rana")
        self.server_socket.send(json.dumps(request_data).encode())
        # print("send success")
        response = json.loads(decrypt(json.loads(self.server_socket.recv(2048).decode()), self.pkda_public_key))
        print(f"[.] 5) RECIEVED KEY{response['message']['public_key']}")

        if "mahansh" not in self.keyList:
            self.keyList["mahansh"] = response['message']['public_key']

    def receive_message(self, step):
        response = json.loads(decrypt(json.loads(self.client_socket.recv(2048).decode()), self.private_key))
        return response

    def send_message(self, createNounce,step,nonce2=None, message=None):
        send_data = self.construct_message(self.client_name)
        nonce=None
        if createNounce==True:
            nonce = self.generate_nonce('mine')
            print(f"generating nonce {nonce} ")
        if nonce2:
            send_data['nonce2'] = nonce2
        if nonce:
            send_data['nonce1']=nonce
        if message:
            send_data['message'] = message
        print(f'sending msg {send_data}')
        self.client_socket.send(json.dumps(encrypt(json.dumps(send_data), tuple(self.keyList['mahansh']))).encode())
        
    
    def dataThread(self):
            try:
                while True:
                    response = self.receive_message(1)
                    myres=response['message'].split()
                    
                    if not response:
                        continue
                    print(f"[.] MESSAGE RECEIVED FROM MAHANSH : {response['message']}")
                    response_send_id = 1 + 1
                    if myres[0]=="GOT":
                        continue
                    self.send_message(False,response_send_id, message=f"GOT IT : {response['message']}")
                            # Handle the received response here as per your requirements
            except Exception as e:
                pass
            # You might want to handle exceptions and possibly reconnect here
    def exchangeKeysY(self):
        self.receive_key()
        self.send_message(True, 3)
        response = self.receive_message( 6)
        print(f"[.] MESSAGE RECEIVED FROM Mahansh: {response}")
        self.validate_response(response)
        self.send_message( False,7, nonce2= response['nonce1'])
        print("key exchange success ------------------------------")
        
    def exchangeKeysN(self):
        response = self.receive_message(3)
        self.receive_key()
        print(f"[.] MESSAGE RECEIVIED FROM MAHANSH WAS {response}")
        self.send_message(True,6, nonce2=response['nonce1'])
        response = self.receive_message(7)
        self.validate_response(response)
        print(f"[.] MESSAGE RECEIVIED FROM MAHANSH WAS  {response}")

        print("key exchange success-----------------------------")

    def run(self,init):
        if init=="I":
            self.exchangeKeysY()
        elif init=="R":
            self.exchangeKeysN()
        else:
            print("wrond command")
            exit()
        self.receive_thread = threading.Thread(target=self.dataThread)
        # self.receive_thread.daemon = True  # Daemonize the thread
        self.receive_thread.start()
        while(True):
            message=input("enter msg to send to mahansh")
            self.send_message(False,1, message=message)
            # response = self.receive_message(1)
            # print(f"[.] MESSAGE RECEIVED FROM MAHANSH: {response['message']}")
if __name__ == "__main__":

    address = ("127.0.0.1", 5678)
    address2 = ("127.0.0.1", 5679)
    init=input("are you initiator or responder I / R")
    pkda_client = PKDAClient(address,address2)
    pkda_client.run(init)
