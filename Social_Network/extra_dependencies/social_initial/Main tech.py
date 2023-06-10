# Import necessary libraries
import hashlib
import json
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request
import requests
from tkinter import *

# Instantiate the GUI
root = Tk()
root.title("Blockchain Social Network")
root.geometry("800x800")

# Define the functions for the GUI
def mine_block():
    response = requests.get("http://localhost:5000/mine")
    message = response.json()["message"]
    update_blockchain_info()
    update_message_info(message)

def add_transaction():
    sender = sender_entry.get()
    recipient = recipient_entry.get()
    amount = amount_entry.get()
    payload = {
        "sender": sender,
        "recipient": recipient,
        "amount": amount
    }
    response = requests.post("http://localhost:5000/transactions/new", json=payload)
    message = response.json()["message"]
    update_blockchain_info()
    update_message_info(message)
    clear_transaction_info()

def view_chain():
    response = requests.get("http://localhost:5000/chain")
    chain = response.json()["chain"]
    chain_info.delete("1.0", END)
    for block in chain:
        chain_info.insert(END, f"Block {block['index']}\n")
        chain_info.insert(END, f"Timestamp: {block['timestamp']}\n")
        chain_info.insert(END, "Transactions:\n")
        for transaction in block["transactions"]:
            chain_info.insert(END, f"    Sender: {transaction['sender']}\n")
            chain_info.insert(END, f"    Recipient: {transaction['recipient']}\n")
            chain_info.insert(END, f"    Amount: {transaction['amount']}\n")
        chain_info.insert(END, f"Proof: {block['proof']}\n")
        chain_info.insert(END, f"Previous Hash: {block['previous_hash']}\n\n")

def update_blockchain_info():
    view_chain()

def update_message_info(message):
    message_label.config(text=message)

def clear_transaction_info():
    sender_entry.delete(0, END)
    recipient_entry.delete(0, END)
    amount_entry.delete(0, END)

# Define the GUI components
blockchain_label = Label(root, text="Blockchain", font=("Arial", 16))
blockchain_label.pack()

chain_info = Text(root, width=80, height=10, font=("Arial", 12))
chain_info.pack()

transaction_label = Label(root, text="Add Transaction", font=("Arial", 16))
transaction_label.pack()

sender_label = Label(root, text="Sender")
sender_label.pack()

sender_entry = Entry(root)
sender_entry.pack()

recipient_label = Label(root, text="Recipient")
recipient_label.pack()

recipient_entry = Entry(root)
recipient_entry.pack()

amount_label = Label(root, text="Amount")
amount_label.pack()

amount_entry = Entry(root)
amount_entry.pack()

add_transaction_button = Button(root, text="Add Transaction", command=add_transaction)
add_transaction_button.pack()

mine_block_button = Button(root, text="Mine Block", command=mine_block)
mine_block_button.pack()

message_label = Label(root, text="", font=("Arial", 12))
message_label.pack()

# Start the GUI
root.mainloop()


# Define the blockchain class
class Blockchain:
    def __init__(self):
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

# Instantiate the Node
app = Flask(__name__)
@app.route('/')
def index():
    return 'Welcome to our social network!'

@app.route('/users/<int:user_id>')
def get_user(user_id):
    # Here you can implement the logic to retrieve the user with the specified ID from the blockchain and return their data as a JSON response.
    # For example:
    user = blockchain.get_user(user_id)
    if user is None:
        return {'error': 'User not found'}, 404
    else:
        return {'id': user.id, 'name': user.name, 'email': user.email}, 200

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()

# Define the endpoints
@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

# Run the app on port 5000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
