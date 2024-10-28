import socket
import threading
import time
import json
import random
from RSA import encrypt

class PKDAserver:
    def __init__(self, address):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(address)
        self.server_socket.listen(5)

        self.private_key=(857393, 365609)
        self.public_key=(857393, 719249)
        self.clients_public_keys = {'mahansh':(578129, 461873),'rana':(732857, 91235)}

        self.my_nonce = set()
        self.others_nonce = set()

        print(f"[.] PKDA SERVER STARTED ON https://{address[0]}:{address[1]}")

    def generate_nonce(self, entity):
        nonce = random.randint(1, 10000)

        while nonce in self.my_nonce or nonce in self.others_nonce:
            nonce = random.randint(1, 10000)

        if entity == 'mine':
            self.my_nonce.add(nonce)
        elif entity == 'others':
            self.others_nonce.add(nonce)
        
        return nonce
    
    def construct_message(self, status,public_key, old_request):
        timestamp = int(time.time())
        duration = 300
        nonce = self.generate_nonce('mine')

        message_data = {
            'status': status,
            'message': {
                'public_key': public_key,
                'old_message': old_request,
                'time': old_request.get('timestamp')
            },
            'timestamp': timestamp,
            'duration': duration,
            'nonce': nonce,
        }

        return message_data

    def get_public_key(self, client_id, old_request):
        public_key = self.clients_public_keys.get(client_id)
        response = self.construct_message('sucess',public_key, old_request )

        return response

    def is_valid_request(self, request_data):
        nonce = request_data.get('nonce')
        timestamp = request_data.get('timestamp')

        if nonce in self.my_nonce or nonce in self.others_nonce:
            print(f"Invalid nonce {nonce} received. Nonce should be unique.")
            return False
        
        current_time = int(time.time())
        if current_time - timestamp > 300: 
            print(f"Request from {request_data.get('sender')} arrived outside the time duration.")
            return False

        return True

    def client_handler(self, client_socket, client_address):
        try:
            print(f"[.] CONNECTING ESTABLISHED WITH {client_address}.")

            received_data = json.loads(client_socket.recv(2048).decode())
            
            if self.is_valid_request(received_data):
                
                requested_id = received_data['requested_id']
                
                response=self.get_public_key(requested_id,received_data)
                print(f"[.] RESPONSE GENERATED {response}\n")

                client_socket.send(json.dumps(encrypt(json.dumps(response), self.private_key)).encode())
                print("[.] RESPONSE SENT SUCCESFULLY")
            
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            client_socket.close()

    def run(self):
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                client_thread = threading.Thread(target=self.client_handler, args=(client_socket, client_address))
                client_thread.start()
            
        except Exception as e:
            print(f"Unexpected error occurred: {e}")

if __name__ == "__main__":
    address = ("127.0.0.1", 5678)
    server = PKDAserver(address)
    server.run()