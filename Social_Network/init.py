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

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "asdfghjkdasdfghjklzxcvbhjkioerfghnujhbfvbvbnmfgbxcvgyuikerthv"


timeout = random.randint(30, 1440)


# Set the session timeout to 24 hours
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=timeout)

# Configure the limiter to allow up to 5 login attempts per minute per IP address
limiter = Limiter(app, default_limits=["5 per minute"])

# Initialising blockchain
blockchain = Blockchain()
# Initialising socketIO
socketio = SocketIO(app)
# Initialising ETE encryption
ete = ETE.ETEEncryption()


@socketio.on('join_room')
def on_join(contact):
     # Get the username and contact name from the data
    username = session['username']
    contact = contact
    # Generate a room name for the contact
    room = f'{username}_{contact}'
    # Join the room
    join_room(room)

@socketio.on('send_message')
def handle_message(data):
    # Get the current contact from the session
    contact = session.get('contact')
    if contact not in session['contacts']:
        return redirect('/')
    
    username = session.get("username")
    try:
        room = session.get('room')
    except KeyError:
        room = f"{username}_{contact}"

    message = data
    content = f"{username}: {message}"
    # Encrypt message using ETE
    encrypted_message = ete.encrypt(content)
    emit(content, room=room)
    session['contacts'][contact]["messages"].append(content)



@app.route('/chat')
def chat():
    if 'username' in session:
        username = session['username']
        contact = request.args.get('contact')
        if session.get("username") is None or contact not in session['contacts']:
            print('contact problem')
            return redirect('/')
        else:
            try:
                room = session.get('room')
            except KeyError:
                room = f"{username}_{contact}"

            join_room(room)

            # Send the contact's message list to the client
            emit(ete.decrypt(json.dumps(session['contacts'][contact]["messages"])))
    else:
        return redirect('/login')

    return render_template("chat.html", contact=contact, messages=session['contacts'][contact]["messages"])
