import string
from collections import defaultdict

import random
from flask import Flask, send_file, request
from tensorflow.python.framework.errors import InvalidArgumentError
from werkzeug.contrib.fixers import ProxyFix
from model import Model
import json
from json import encoder
import numpy as np
encoder.FLOAT_REPR = lambda o: format(o, '.3f')

app = Flask(__name__)
model = Model()

ADMINS = ['exthran@gmail.com']
if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler('localhost', 'pid-error@thran.cz', ADMINS, 'Plant ID Failed')
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)


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
    response = {"images": [], "suggestions": defaultdict(lambda: [])}
    for _, file in sorted(request.files.items(), key=lambda x: x[0]):
        crops = 1
        strategy = request.args.get('strategy', 'fast')
        similar_count = int(request.args.get('similar_count', '0'))
        if strategy == 'fast':
            crops = 1
        if strategy == 'medium':
            crops = 5
        if strategy == 'slow':
            crops = 9
        if strategy == 'extra_slow':
            crops = 19
        try:
            ids, certainties, similar = model.identify_plant(file.read(), request.form, crops=crops, similar_count=similar_count)
        except (InvalidArgumentError, SystemError) as err:
            return str(err).split("\n")[0], 400
        plants = {}
        for i, (plant, prob) in enumerate(sorted(ids.items(), key=lambda x: x[1], reverse=True)):
            p = prob * certainties["listed"]
            if i == 0:
                p = max(p, certainties["1st"])
            plants[plant] = p
            response["suggestions"][plant].append(p)
        response["images"].append({
            "plants": plants,
            "raw_predictions": ids,
            "certainties": certainties,
            "similar": similar,
        })
    for plant, probs in response["suggestions"].items():
        response["suggestions"][plant] = 1 - np.product(1 - np.array(probs))
    return json.dumps(response)


app.wsgi_app = ProxyFix(app.wsgi_app)
if __name__ == '__main__':
    app.debug = True
    app.run()
