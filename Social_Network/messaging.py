from flask import Flask, request, render_template, redirect, session, abort
from blockchain_alt import Blockchain
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask_limiter import Limiter
from datetime import datetime, timedelta
import requests
import json
import random
import encryption.ETE as ETE
import pytz
from pubnub.pubnub import PubNub
from pubnub.enums import PNStatusCategory, PNOperationType
from pubnub.pnconfiguration import PNConfiguration
from pubnub.callbacks import SubscribeCallback


app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "asdfghjkdasdfghjklzxcvbhjkioerfghnujhbfvbvbnmfgbxcvgyuikerthv"

# Setting up pubnub
pnconfig = PNConfiguration()
pnconfig.subscribe_key = 'sub-c-c1c09cbf-6591-43b8-b716-8986a74d3339'
pnconfig.publish_key = 'pub-c-73172311-d8ce-499e-ab72-c1de92e266b4'
pnconfig.ssl = True

pubnub = PubNub(pnconfig)

# Initialising ETE encryption
ete = ETE.ETEEncryption()

class MySubscribeCallback(SubscribeCallback):
    def presence(self, pubnub, presence):
        pass  # handle incoming presence data

    def status(self, pubnub, status):
        if status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
            print("Disconnected from PubNub")

        elif status.category == PNStatusCategory.PNConnectedCategory:
            print("Connected to PubNub")
            # You can use the connected event to subscribe to channels and start publishing messages
            pubnub.subscribe().channels('my_channel').execute()

        elif status.category == PNStatusCategory.PNReconnectedCategory:
            print("Reconnected to PubNub")

        elif status.category == PNStatusCategory.PNDecryptionErrorCategory:
            print("Error decrypting message")

    def message(self, pubnub, message):
        # Handle new message stored in message.message
        print(message.message)

@app.route('/send', methods=['POST'])
def send():
    # get the message and the current contact from the form data
    message = request.form['message']
    contact = session['contact']

    # encrypt the message using ETE
    encrypted_message = ete.encrypt(message)

    # publish the encrypted message to the current contact's channel
    pubnub.publish().channel('channel_' + contact).message(encrypted_message).sync()

    return '', 204


@app.route('/chat/<contact>')
def chat(contact):
    # set up the session for the current contact
        if 'username' in session:
            username = session['username']
            # contact = request.args.get('contact')
            if session.get("username") is None or contact not in session['contacts']:
                print('contact problem')
                return redirect('/')
            else:
                session['contact'] = contact

                # subscribe to the channel for the current contact
                pubnub.add_listener(MySubscribeCallback())
                pubnub.subscribe().channels('channel_' + contact).execute()

                return render_template('chat.html', contact=contact)
        else:
            return redirect('/login')
