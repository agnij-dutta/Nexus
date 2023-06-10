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
def start():
    root.mainloop()