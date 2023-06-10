from flask import Flask, request, render_template, redirect, session, abort
from blockchain_alt import Blockchain, UserBlock
from flask_socketio import SocketIO, send, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import socket
import threading
from datetime import datetime, timedelta
import requests
import random
import encryption.ETE as ETE
import pytz
import json
from flask.json import JSONEncoder
# from dotenv import load_dotenv
# from flask_cors import CORS

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


@app.before_request
def check_tor():
    """
    Check if the request is coming from a Tor exit node
    """
    exit_nodes = set()
    response = requests.get('https://check.torproject.org/exit-addresses')
    for line in response.iter_lines():
        if line.startswith(b'ExitAddress '):
            exit_nodes.add(line.split()[1].decode())
    if request.remote_addr in exit_nodes:
        abort(403)


@app.before_request
def check_session_timeout():
    # Get the user's last activity time from the session
    last_activity = session.get('last_activity')

    # If the user's session has timed out, log them out and redirect them to the login page
    if last_activity is not None and (datetime.now(pytz.utc) - last_activity) > app.config['PERMANENT_SESSION_LIFETIME']:
        return redirect('/logout/')

    # Set the user's last activity time to the current time
    session['last_activity'] = datetime.now()


def get_current_block():
    for block in blockchain.chain:
        if isinstance(block, UserBlock)  and block.username == session['username']:
            blockchain.current_block = block

def update_global():
    get_current_block()
    blockchain.current_block.contacts = session['contacts']
    blockchain.current_block.key = session['key']
    blockchain.update_chain()


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    blockchain.load_chain()
    message = ''
    print(blockchain.used_names)
    if request.method == 'POST':
        username = request.form.get('name')
        key = request.form.get('key')
        print(blockchain.used_names)
        if username not in blockchain.used_names.keys():
            print("bal")
            try:
                blockchain.add_user(username=username, key=key, ip=get_remote_address(), port=str(request.environ['REMOTE_PORT']))
                blockchain.update_chain()
                blockchain.load_chain()
                print(blockchain.used_names)
                return redirect('/login')
            except Exception:
                message = "Failed to signup!"
        else:
            message = "User already exists! Please choose another name."
    return render_template('signup.html', message=message)



@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("1 per minute")
def login():
    session.clear()
    message = ''
    #blockchain.load_chain()
    if request.method == 'POST':
        # get username from request
        username = request.form.get('name')
        session['username'] = username
        key = request.form.get('key')
        #logging in the user if user is in the blockchain
        login_auth = blockchain.login_user(username, key)
        if login_auth == True:
            session['key'] = key
            session['contacts'] = blockchain.current_block.contacts
            session['index'] = blockchain.current_block.index
            if get_remote_address() == blockchain.current_block.ip:
                session['ip'] = blockchain.current_block.ip
                session['user'] = Peer(session['username'], blockchain.current_block.ip, request.environ['REMOTE_PORT'])
            else:
                blockchain.current_block.ip = get_remote_address()
                session['ip'] = blockchain.current_block.ip
                blockchain.used_names[session['username']][0] = blockchain.current_block.ip
                session['user'] = Peer(session['username'], blockchain.current_block.ip, request.environ['REMOTE_PORT'])
                
                # Updating the global blockchain
                update_global()

            # Set the user's session cookie to permanent
            session.permanent = True

            # Set the user's last activity time to the current time
            session['last_activity'] = datetime.now()

            return redirect('/')
        else:
            message = 'Failed to login!'
    return render_template('login.html', message=message)


@app.route('/', methods=['GET', 'POST'])
def home():
     # Checking authenticated user
    if 'username' in session:
        username = session['username']

        # Creating list of contacts t display on the frontend
        contacts = list(session['contacts'].keys())
        if request.method == 'POST':

            # Taking search query to find a contact
            search = request.form.get('search')

            if search in contacts:
                session['current_contact'] = search
                return redirect('/chat/')

        return render_template('home.html', contacts=contacts)
    else:
        return redirect('/login')


@app.route("/logout/")
def logout():
    session.clear()
    return redirect('/')


@app.route('/add_contact/', methods=['GET', 'POST'])
def add_contact():
    # Checking authenticated user
    if 'username' in session:
        random_users = []
        for i in range(len(list(blockchain.used_names.keys()))):
            random_users.append(random.choice(list(blockchain.used_names.keys())))
        random_users = list(set(random_users))
        # print(random_users)
        # print(session['username'])
        # print(str(session['user']))
        # print(blockchain.current_block)
        message = ''
        if request.method == 'POST':
            name  = request.form.get('search')
            user = session.get('username')
            if (len(name) and len(user)) and name in blockchain.used_names and name not in session['contacts']:
                contact = name
                
                # Create peer
                session['contacts'][contact] =  {"messages":[], "peers":(str(session['user']), str(Peer(name, blockchain.used_names[name][0], request.environ['REMOTE_PORT'])))}
                
                # Update global blockchain
                update_global()
                message = "Contact added successfully!"

            else:
                message = 'Failed to add contact!'
    else:
        return redirect('/login')


    return render_template('create_contact.html', message=message, random_users=random_users)


class Peer:
    def __init__(self, name, ip_address, port):
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected_peers = [username for username in list(blockchain.used_names.keys())]
        self.lock = threading.Lock()

    def start(self):
        self.socket.bind((self.ip_address, self.port))
        self.socket.listen()
        while True:
            conn, addr = self.socket.accept()
            threading.Thread(target=self.handle_connection, args=(conn,)).start()

    def handle_connection(self, conn):
        data = conn.recv(1024)
        message = data.decode('utf-8')
        message_parts = message.split(':')
        sender = message_parts[0]
        recipient = message_parts[1]
        message_text = message_parts[2]
        if recipient == self.name:
            emit('message', {'sender': sender, 'recipient': recipient, 'message': message_text}, room=self.name)
        else:
            self.forward_message(message)

    def forward_message(self, message):
        for peer in self.connected_peers:
            if peer != self.name:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((peer.ip_address, peer.port))
                    s.send(message.encode('utf-8'))
                    s.close()
                except:
                    pass

    def connect_to_peer(self, peer):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((peer.ip_address, peer.port))
            s.send(f'{self.name}:{peer.name}:Hello'.encode('utf-8'))
            s.close()
            self.connected_peers.append(peer.name)
        except:
            pass

    def to_dict(self):
        return {'name': self.name, 'ip': self.ip_address, 'port': self.port, 'peers': self.connected_peers}


class PeerEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Peer) or isinstance(obj, UserBlock):
            return obj.to_dict()  # replace this with your own serialization logic
        return super().default(obj)

# Encoding peer object using the PeerEncoder class
app.json_encoder = PeerEncoder

# Sending messages to the specified peer using socketio

@socketio.on('send_message')
def send_message(data):
    recipient = data['recipient']
    message_text = data['message']
    message = f'{socketio.sid}:{recipient}:{message_text}'
    peers = session['contacts'][recipient]["peers"]
    for peer in [peers]:
        if peer.name == socketio.sid:
            sender = peer
            break
    sender.forward_message(message)

@app.route('/chat/',  methods=['GET', 'POST'])
def chat(): 
    if 'username' in session:
        username = session['username']
        ##contact = None  # Initialising the contact variable

        # Checking for selected contact in session
        try:
            contact = session['current_contact']
            print(session['current_contact'])
        except KeyError:
            print("key not found")
            return redirect('/')
        contact = session['current_contact'] 
        print(contact)
        if session.get("username") is None or session['current_contact']  not in session['contacts'] or contact is None:
            print(session['current_contact'] )
            print('contact problem')
            return redirect('/')
        else:
            contact = session['current_contact'] 
            text = request.args.get("Enter message...")
            if text:
                data = {
                    'recepient': session['current_contact'] ,
                    'sender': username,
                    'message': text,
                    'timestamp': str(datetime.now())
                    }
                socketio.emit('send_message', data)
                session['contacts'][session['current_contact'] ]["messages"].append(data)
                print(session['contacts'][session['current_contact'] ]["messages"])
                update_global() 
            # print(session['current_contact'])
            data = {
                'recepient': session['current_contact'] ,
                'sender': username,
                'message': text,
                'timestamp': str(datetime.now())
                }
            print(text)
            print(data)
            
        return render_template("chat.html",username=username, contact=session['current_contact'] , messages=session['contacts'][session['current_contact'] ]["messages"], recipient_ip=blockchain.used_names[session['current_contact'] ][0], recipient_port=blockchain.used_names[session['current_contact'] ][1], data=data)
    else:
        return redirect('/login')
    


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
