# Importing the necessary libraries
from uuid import uuid4
from flask import Flask, jsonify, request, render_template, redirects
import requests
import blockchain
import app_GUI
# Instantiate the Node
app = Flask(__name__)
app.secret_key = "sfdjkafnk"
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
    app_GUI.start()