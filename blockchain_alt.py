# Import required libraries
import hashlib
import datetime as date
import functools
import os
import sys
import firebase_admin
from firebase_admin import db
from firebase_admin import credentials
# Importing my own encrption file and necessary libraries
import encrypt
import base64
import json

cred = credentials.Certificate("C:/Users/Anutosh/Desktop/Social_Network/nexus-online-firebase-adminsdk-msrak-5553de8c19.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://nexus-online-default-rtdb.asia-southeast1.firebasedatabase.app'
})
db_ref = db.reference()

# Set up Firebase project credentials
firebase_api_key = "AIzaSyAYMV0EfRZl8AUsruuEPZ085oTUBX4bfMc"
firebase_project_id = "nexus-online"

hashseed = os.getenv('PYTHONHASHSEED')

if not hashseed:
    os.environ['PYTHONHASHSEED'] = '0'
    os.execv(sys.executable, [sys.executable] + sys.argv)

#defining the parent class
class Block:
    def __init__(self, index, timestamp, previous_hash, key):
        self.key = key
        self.index = index
        self.timestamp = str(timestamp)
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        data = str(self.index) + str(self.timestamp) + str(self.key) + str(self.previous_hash) + str(self.nonce)
        data = data.strip()
        return hashlib.sha256((data).encode('utf-8')).hexdigest()
    
    def mine_block(self, difficulty):
     target = '0' * difficulty
     while True:
        self.nonce += 1
        guess = self.calculate_hash()
        self.hash = guess
        if guess[:difficulty] == target:
            return self.nonce
    
    def validate_block(self, difficulty):
        target = '0' * difficulty
        return self.hash[:difficulty] == target

#Child class 1: Handles users as blocks
class UserBlock(Block):
    def __init__(self, index, timestamp, previous_hash, username, key, ip, port, contacts = dict()):
        self.username = username
        self.port = port
        self.timestamp = timestamp
        self.ip = ip
        self.key = key
        self.contacts = contacts
        self.data = {
            "key": self.key,
            "contacts": str(self.contacts)
          }
        super().__init__(index, timestamp, previous_hash, self.key)



# Define the Blockchain class
class Blockchain:
    def __init__(self, difficulty=2):
        self.difficulty = difficulty
        self.used_names = {}
        self.user_ids = []
        self.chain = self.load_chain()
        if not self.validate_chain():
            pass
        if len(self.chain) > 216:
            difficulty += 1

        self.current_block = None
    
    @functools.lru_cache(maxsize=128)
    def load_chain(self):
        chain = []
        db_ref = db.reference('user_blocks')
        blocks_data = db_ref.get()
        if blocks_data:
           for user_id in blocks_data:
                block_data = blocks_data[user_id]
                block = UserBlock(
                    index=block_data['index'],
                    ip= block_data['ip_address'],
                    timestamp=block_data['timestamp'],
                    port=block_data['port'],
                    key = "", 
                    previous_hash=block_data['previous_hash'],
                    username=block_data['username']
                )
                self.used_names[block_data['user_name']] = [block_data['ip_address'], block_data['port']]
                self.user_ids.append(user_id)
                block.data = block_data['data']
                block.hash = block_data['hash']
                block.nonce = block_data['nonce']
                chain.append(block)
        else:
            pass
        chain = sorted(chain, key=lambda b: b.index)
        return chain


    def add_user(self, username, key, ip, port):
        previous_block = self.chain[-1]
        index = previous_block.index + 1
        timestamp = date.datetime.now()
        self.validate_chain()   
        block = UserBlock(index, timestamp, previous_block.hash, username=username, key=key, ip=ip, port=port)
        block.mine_block(self.difficulty)
        encrypted_dict = encrypt.encrypt_dict(json.dumps(block.data), key)
        encrypted_dict = base64.b64encode(encrypted_dict).decode()
        block.data = encrypted_dict
        self.chain.append(block)
        if self.validate_chain():
            block_dict = {
            'username': block.username,
            'ip_address': block.ip,
            'port': block.port,
            'index': block.index,
            'timestamp': block.timestamp,
            'data': block.data,
            'previous_hash': block.previous_hash,
            'nonce': block.nonce,
            'hash': block.hash
        }
            db_ref.child("user_blocks").push(block_dict)
            
        else:
            print("Cannot add block")
        

    def get_latest_block(self):
        return self.chain[-1]

    def get_blockchain(self):
        chain_data = []
        for block in self.chain:
            chain_data.append(block.__dict__)
        return chain_data
    
    def validate_chain(self):
        previous_hash = None
        for block in self.chain:
            if not block.validate_block(self.difficulty):
                print("block problem")
                return False
            # check if the previous_hash of the current block is the hash of the previous block
            if previous_hash is not None and block.previous_hash != previous_hash:
                print("previous hash problem")
                return False
            previous_hash = block.hash
        return True
    
    def login_user(self, username, key):
    # Check if the username exists in the blockchain
        for block in self.chain:
            if isinstance(block, UserBlock)  and block.username == username:
                try:
                    #decrypting the block data
                    block_data = base64.b64decode(block.data)
                    block_data = encrypt.decrypt_dict(block_data, key)
                    block.data = block_data
                    
                    # Calculate the hash of the user block using the given password
                    data = str(block.index) + str(block.timestamp) + str(key) + str(block.previous_hash) + str(block.nonce)
                    data = data.strip()
                    hash = hashlib.sha256((data).encode('utf-8')).hexdigest()

                    # Check if the calculated hash matches the hash of the user block
                    if hash == block.hash:
                        block.key = key
                        block.contacts = eval(block.data['contacts'])
                        self.current_block = block
                        self.current_block.ip = block.ip
                        self.current_block.port = block.port
                        self.current_block.contacts = block.contacts
                        self.current_block.index = block.index
                        return True
                    else:
                        print("hash not matching")
                        return False
                except Exception:
                    print('incorrect key')
                    return False
        
        return False
    
    def update_chain(self):
       db_ref = db.reference('user_blocks')
       if self.current_block != None:
        if self.current_block.username in self.used_names:
            index = self.used_names.index(self.current_block.username)
            user_id = self.user_ids[index]  
            data = {
            "key": self.current_block.key,
            "contacts": str(self.current_block.contacts)
          }

            # Encrypting the current data
            encrypted_dict = encrypt.encrypt_dict(json.dumps(data), self.current_block.key)
            encrypted_dict = base64.b64encode(encrypted_dict).decode()

            self.contacts = dict()
            self.key = ''

            self.current_block.data = encrypted_dict
            self.chain[self.current_block.index] = self.current_block

            if self.validate_chain():
                block_dict = {
                'username': self.current_block.username,
                'ip': self.current_block.ip,
                'port': self.current_block.port,
                'index': self.current_block.index,
                'timestamp': self.current_block.timestamp,
                'data': self.current_block.data,
                'previous_hash': self.current_block.previous_hash,
                'nonce': self.current_block.nonce,
                'hash': self.current_block.hash
            }
                db_ref.child(user_id).set(block_dict)
                print('done')
            else:
                print('not done')


if __name__ == '__main__':
    blockchain = Blockchain()
    # blockchain.add_user('gogol', key = '040kakuksksk5hs6')
    # blockchain.add_user('agnij', key = 'duttalakssoo0dr2')
    logina = blockchain.login_user('gogol', '040kakuksksk5hs6')
    # print(blockchain.get_blockchain())
    print(blockchain.current_block.username)
    # blockchain.add_user('layba', key = 'qwertykdowls2534')
    blockchain.current_block.contacts['admin'] = {"messages":[]}
    blockchain.update_chain()
    # loginb = blockchain.login_user('agnij', 'duttalakssoo0dr2')
    # blockchain.current_block.contacts['admin'] = {"messages":[]}
    # blockchain.update_chain()
    # print(logina)
    # print(loginb)
    print(blockchain.get_blockchain())
    # login_admin = blockchain.login_user('admin', 'heathcliff')
    # print(blockchain.current_block.username)
    # print(blockchain.current_block.hash)
    # print(login_admin)
    # print(blockchain.validate_chain())
    # print(blockchain.get_blockchain()) 
    # print(blockchain.get_latest_block())
