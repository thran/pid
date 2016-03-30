import json

import tensorflow as tf
import os

MODEL_FILE = "model.pb"
CLASSES_FILE = "classes.json"
BASE_DIR = os.path.dirname(__file__)

JPEG_DATA_TENSOR_NAME = 'DecodeJpeg/contents:0'
LAT_TENSOR_NAME = 'lat_placeholder:0'
LNG_TENSOR_NAME = 'lng_placeholder:0'
WEEK_TENSOR_NAME = 'week_placeholder:0'


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
            self.lat_placeholder = self.graph.get_tensor_by_name(LAT_TENSOR_NAME)
            self.lng_placeholder = self.graph.get_tensor_by_name(LNG_TENSOR_NAME)
            self.week_placeholder = self.graph.get_tensor_by_name(WEEK_TENSOR_NAME)

    def predict(self, image, meta):
        with self.graph.as_default():
            with tf.Session() as sess:
                feed_dict = {
                    self.image_data_placeholder: image,
                    self.lat_placeholder: meta.get("lat", 0),
                    self.lng_placeholder: meta.get("lng", 0),
                    self.week_placeholder: meta.get("week", 0),
                    "Placeholder:0": 1,
                }
                return sess.run(self.result_tensor, feed_dict=feed_dict)[0]

    def identify_plant_file(self, jpeq_file_path, meta, threshold=0.01):
        image = tf.gfile.FastGFile(jpeq_file_path, 'rb').read()
        self.identify_plant(image, meta)

    def identify_plant(self, image, meta, threshold=0.01):
        prediction = self.predict(image, meta)
        bests = {}
        for pred, cls in zip(prediction, self.classes):
            if pred >= threshold:
                bests[cls] = float(pred)
        return bests
