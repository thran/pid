import json

import tensorflow as tf
import os

MODEL_FILE = "model.pb"
CLASSES_FILE = "classes.json"
JPEG_DATA_TENSOR_NAME = 'DecodeJpeg/contents:0'
BASE_DIR = os.path.dirname(__file__)


class Model:
    def __init__(self):
        with open(os.path.join(BASE_DIR, CLASSES_FILE)) as f:
            self.classes = json.load(f)
        with tf.Session() as sess:
            model_filename = os.path.join(BASE_DIR, MODEL_FILE)
            with tf.gfile.FastGFile(model_filename, 'rb') as f:
                graph_def = tf.GraphDef()
                graph_def.ParseFromString(f.read())
                _ = tf.import_graph_def(graph_def, name='')
            self.graph = sess.graph
            self.result_tensor = self.graph.get_tensor_by_name('final_result:0')
            self.image_data_placeholder = self.graph.get_tensor_by_name(JPEG_DATA_TENSOR_NAME)

    def predict(self, image):
        with self.graph.as_default():
            with tf.Session() as sess:
                return sess.run(self.result_tensor, feed_dict={self.image_data_placeholder: image, "Placeholder:0": 1})[0]

    def identify_plant_file(self, jpeq_file_path, threshold=0.01):
        image = tf.gfile.FastGFile(jpeq_file_path, 'rb').read()
        self.identify_plant(image)

    def identify_plant(self, image, threshold=0.01):
        prediction = self.predict(image)
        bests = {}
        for pred, cls in zip(prediction, self.classes):
            if pred >= threshold:
                bests[cls] = float(pred)
        return bests
