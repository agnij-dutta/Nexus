import hashlib
import json
from time import time
from uuid import uuid4

from flask import Flask, jsonify, request, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, NumberRange
from tkinter import *
from tkinter import ttk
from tkinter import messagebox

root = Tk()
root.title("Simple Shopping List App")
root.geometry("400x300")
root.resizable(False, False)

# create frame for listbox and scrollbar
list_frame = Frame(root)
list_frame.pack(pady=10)

# create scrollbar
scrollbar = Scrollbar(list_frame)
scrollbar.pack(side=RIGHT, fill=Y)

# create listbox
listbox = Listbox(list_frame, width=40, height=10, yscrollcommand=scrollbar.set)
listbox.pack(side=LEFT, fill=BOTH)
scrollbar.config(command=listbox.yview)

# create frame for entry and buttons
button_frame = Frame(root)
button_frame.pack(pady=10)

# create entry
item_entry = ttk.Entry(button_frame, width=30)
item_entry.pack(side=LEFT, padx=5)



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


# Define the user class
class User:
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email


# Instantiate the Node
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'

# Instantiate the Blockchain
blockchain = Blockchain()

# Define the endpoints
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/users', methods=['GET'])
def users():
    users = blockchain.users.values()
    return render_template('users.html', users=users)

@app.route('/users/new', methods=['GET', 'POST'])
def new_user():
    form = NewUserForm()
    if form.validate_on_submit():
        id = form.id.data
        name = form.name.data
        email = form.email.data
        user = User(id=id, name=name, email=email)
        blockchain.add_user(user)
       
def add_item():
    new_item = item_entry.get()
    if new_item:
        items.append(new_item)
        listbox.insert(END, new_item)
        item_entry.delete(0, END)
    else:
        messagebox.showwarning("Invalid Input", "Please enter a valid item.")

add_button = ttk.Button(button_frame, text="Add", command=add_item)
add_button.pack(side=LEFT, padx=5)

def delete_item():
    selection = listbox.curselection()
    if selection:
        index = selection[0]
        item = listbox.get(index)
        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {item}?")
        if confirm:
            listbox.delete(index)
            items.remove(item)
    else:
        messagebox.showwarning("No Selection", "Please select an item to delete.")

delete_button = ttk.Button(button_frame, text="Delete", command=delete_item)
delete_button.pack(side=LEFT, padx=5)

root.mainloop()