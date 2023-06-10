from flask import Flask, render_template, request

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "asdfghjkdasdfghjklzxcvbhjkioerfghnujhbfvbvbnmfgbxcvgyuikerthv"


@app.route('/', methods=['GET', 'POST'])
def index():
    message = "fuck off"
    print(request.remote_addr, request.environ["REMOTE_PORT"])
    return render_template('login.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)
