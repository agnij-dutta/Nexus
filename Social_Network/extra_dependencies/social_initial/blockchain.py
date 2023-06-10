# Import necessary libraries
import hashlib
import json
from time import time
from uuid import uuid4

class Block:
    def __init__(self, previous_block_hash, transaction_list):
        self.previous_block_hash = previous_block_hash
        self.transaction_list = transaction_list

        self.block_data = "-".join(transaction_list) + "-" + previous_block_hash
        self.block_hash = hashlib.sha256(self.block_data.encode()).hexdigest()


#hypothetical list of users
users = ['agnij', 'annie', 'armin', 'mikasa', 'eren', 'levi', 'connie', 'jean', 'erwin', 'hange', 'sasha', 'reiner']

block_members = []
for user in users:
    if len(block_members) < 2:
        block_members.append(user)
        users.remove(user)

block1 = Block("", block_members)

# Define the blockchain
class Blockchain:
    def __init__(self, blocks):
        self.chain = []
        self.current_transactions = []
        self.users = {}

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)


    def add_user(self, user):
        self.users[user.id] = user

    def get_user(self, user_id):
        if user_id in self.users:
            return self.users[user_id]
        else:
            return None


    def new_block(self, proof, previous_hash=None):
        # Creates a new Block and adds it to the chain
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block


    def new_transaction(self, sender, recipient, amount):
        # Adds a new transaction to the list of transactions
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1


    @staticmethod
    def hash(block):
        # Hashes a Block
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


    @property
    def last_block(self):
        # Returns the last Block in the chain
        return self.chain[-1]


    def proof_of_work(self, last_proof):
        # Simple Proof of Work Algorithm:
        # - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
        # - p is the previous proof, and p' is the new proof
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof


    @staticmethod
    def valid_proof(last_proof, proof):
        # Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

