import random
from Crypto.Util.number import getPrime


def encrypt(message, public_key):
    n, e = public_key
    cipher = [pow(ord(char), e, n) for char in message]
    return cipher

def decrypt(cipher, private_key):
    n, d = private_key
    message = ''.join([chr(pow(char, d, n)) for char in cipher])
    return message