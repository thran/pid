from flask import Flask, send_file
from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__)


@app.route('/')
def hello_world():
    return send_file('templates/home.html')


app.wsgi_app = ProxyFix(app.wsgi_app)
if __name__ == '__main__':
    app.run()
