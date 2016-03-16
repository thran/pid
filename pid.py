import string
import random
import os
from flask import Flask, send_file, request
from werkzeug.contrib.fixers import ProxyFix
from model import Model
import json
from json import encoder
encoder.FLOAT_REPR = lambda o: format(o, '.3f')

app = Flask(__name__)
model = Model()


@app.route('/')
def home():
    return send_file('templates/home.html')


@app.route('/classes')
def classes():
    return send_file('classes.json')


def random_string(length=10):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))


@app.route('/identify', methods=['POST'])
def identify():
    file = request.files["file"]
    ids = model.identify_plant(file.read())
    return json.dumps(ids)


app.wsgi_app = ProxyFix(app.wsgi_app)
if __name__ == '__main__':
    app.debug = True
    app.run()
