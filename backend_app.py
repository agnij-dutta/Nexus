from flask import Flask, request, render_template, redirect, session, abort
from blockchain_alt import Blockchain
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import socket
import threading
from datetime import datetime, timedelta
import requests
import random
import ETE
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


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    message = ''
    if request.method == 'POST':
        username = request.form.get('name')
        key = request.form.get('key')
        print(blockchain.used_names)
        if username not in list(blockchain.used_names.keys()):
            try:
                blockchain.add_user(username=username, key=key, ip=get_remote_address())
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
    if request.method == 'POST':
        # get username from request
        username = request.form.get('name')
        session['username'] = username
        key = request.form.get('key')
        #logging in the user if user is in the blockchain
        login_auth = blockchain.login_user(username, key)
        if login_auth == True:
            session['contacts'] = blockchain.current_block.contacts
            session['index'] = blockchain.current_block.index
            session['user'] = Peer(session[username], get_remote_address(), request.environ['REMOTE_PORT'])
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
    if 'username' in session:
        username = session['username']
        contacts = list(session['contacts'].keys())
        print(contacts)
        if request.method == 'POST':
            search = request.form.get("name")
            if not search:
                return render_template('home.html', contacts=contacts)
            else:
                room = f"{username}_{search}"
                return redirect('/chat')

        return render_template('home.html', contacts=contacts)
    else:
        return redirect('/login')


@app.route("/logout/")
def logout():
    session.clear()
    return redirect('/')


@app.route('/add-contact/', methods=['GET', 'POST'])
def add_contact():
    if 'username' in session:
        message = ''
        if request.method == 'POST':
            name  = request.form.get('username')
            user = session.get('username')
            if (len(name) and len(user)) and name in blockchain.used_names:
                contact = name
                # create peer
                session['contacts'][contact] =  {"messages":[]}

                # Emit a message to the contact to inform them of the new room
                emit('new_contact', {'username': user}, room=room)

                blockchain.current_block.contacts = session['contacts']
                blockchain.update_chain()
            else:
                message = 'Failed to add contact!'
        else:
            return redirect('/login')

    return render_template('create_contact.html', message=message)


class Peer:
    def __init__(self, name, ip_address, port):
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected_peers = []
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



@socketio.on('send_message')
def send_message(data):
    recipient = data['recipient']
    message_text = data['message']
    message = f'{socketio.sid}:{recipient}:{message_text}'
    for peer in [peers]:
        if peer.name == socketio.sid:
            sender = peer
            break
    sender.forward_message(message)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
