import json

import numpy as np
import tfdeploy as td
import tensorflow as tf
import os

MODEL_FILE = "model.pb"
CERTAINTY_MODEL_FILE = "certainty_model.pkl"
CLASSES_FILE = "classes.json"
BASE_DIR = os.path.dirname(__file__)

JPEG_DATA_TENSOR_NAME = 'jpeg:0'
IMAGE_TENSOR_NAME = 'pre_process_image/convert_image:0'
RESULT_TENSOR_NAME = 'results/predictions:0'
LAT_TENSOR_NAME = 'lat_placeholder:0'
LNG_TENSOR_NAME = 'lng_placeholder:0'
WEEK_TENSOR_NAME = 'week_placeholder:0'
LAST_HIDDEN_TENSOR_NAME = 'inception_v3/logits/flatten/Reshape:0'


class CertaintyModel:
    def __init__(self):
        self.model = td.Model(os.path.join(BASE_DIR, CERTAINTY_MODEL_FILE))
        self.input, self.output = self.model.get("row_predictions", "output/certainties")

    def get_certainty(self, input):
        return self.output.eval({self.input: sorted(input)})


def crop_image(image, crop):
    height, width, _ = image.shape

    if crop == 'no_crop':
        pass
    if crop.startswith('left'):
        if height >= width:
            image = image[:width, :, :]
        else:
            image = image[:, :height, :]
    if crop.startswith('center'):
        if height >= width:
            image = image[(height - width)/2:(height + width)/2, :, :]
        else:
            image = image[:, (width - height)/2:(height + width)/2, :]
    if crop.startswith('right'):
        if height >= width:
            image = image[-width:, :, :]
        else:
            image = image[:, -height:, :]

    height, width, _ = image.shape
    if crop.endswith('_center'):
        image = image[int(height * .15):int(height * .85), int(height * .15):int(height * .85), :]
    if crop.endswith('_top_left'):
        image = image[:int(height * .7), :int(height * .7), :]
    if crop.endswith('_top_right'):
        image = image[:int(height * .7), int(height * .3):, :]
    if crop.endswith('_bottom_left'):
        image = image[int(height * .3):, :int(height * .7), :]
    if crop.endswith('_bottom_right'):
        image = image[int(height * .3):, int(height * .3):, :]

    return image


def normalize(vectors):
    if len(vectors.shape) == 1:
        return (vectors.T - vectors.mean()) / vectors.std()
    return ((vectors.T - vectors.mean(axis=1)) / vectors.std(axis=1)).T


class Model:
    crops = [
        'no_crop', 'center_center', 'center', 'right', 'left',
        'center_top_left', 'center_top_right', 'center_bottom_left', 'center_bottom_right'
        'left_center', 'left_top_left', 'left_top_right', 'left_bottom_left', 'left_bottom_right'
        'right', 'right_top_left', 'right_top_right', 'right_bottom_left', 'right_bottom_right'
    ]

    def __init__(self):
        self.certainty_model = CertaintyModel()
        with open(os.path.join(BASE_DIR, CLASSES_FILE)) as f:
            self.classes = json.load(f)
        with tf.Session() as sess:
            model_filename = os.path.join(BASE_DIR, MODEL_FILE)
            with tf.gfile.FastGFile(model_filename, 'rb') as f:
                graph_def = tf.GraphDef()
                graph_def.ParseFromString(f.read())
                _ = tf.import_graph_def(graph_def, name='')
            self.graph = sess.graph
            self.result_tensor = self.graph.get_tensor_by_name(RESULT_TENSOR_NAME)
            self.raw_predictions_tensor = self.result_tensor.op.inputs[0]
            self.image_data_placeholder = self.graph.get_tensor_by_name(JPEG_DATA_TENSOR_NAME)
            self.image = self.graph.get_tensor_by_name(IMAGE_TENSOR_NAME)
            self.lat_placeholder = self.graph.get_tensor_by_name(LAT_TENSOR_NAME)
            self.lng_placeholder = self.graph.get_tensor_by_name(LNG_TENSOR_NAME)
            self.week_placeholder = self.graph.get_tensor_by_name(WEEK_TENSOR_NAME)
            self.last_hidden = self.graph.get_tensor_by_name(LAST_HIDDEN_TENSOR_NAME)

            self.jpeg = tf.placeholder(dtype='string')
            image = tf.image.decode_jpeg(self.jpeg, channels=3)
            self.decoded_image = tf.image.convert_image_dtype(image, dtype=tf.float32)

            self.embeddings_meta = np.load(os.path.join(BASE_DIR, 'embeddings_meta.npy'))
            self.embeddings = normalize(np.load(os.path.join(BASE_DIR, 'embeddings.npy')))

    def predict(self, sess, image, meta):
        feed_dict = {
            self.image: image,
            self.lat_placeholder: meta.get("lat", 0),
            self.lng_placeholder: meta.get("lng", 0),
            self.week_placeholder: meta.get("week", 0),
        }
        return [x[0] for x in sess.run([self.result_tensor, self.raw_predictions_tensor, self.last_hidden], feed_dict=feed_dict)]

    def identify_plant_file(self, jpeq_file_path, meta, threshold=0.05):
        image = tf.gfile.FastGFile(jpeq_file_path, 'rb').read()
        self.identify_plant(image, meta)

    def identify_plant(self, image, meta, crops=1, threshold=0.05, similar_count=0):
        with self.graph.as_default():
            with tf.Session() as sess:
                image = sess.run(self.decoded_image, {self.jpeg: image})

                crops = self.crops[:min(crops, len(self.crops))]
                row_mean = np.zeros(len(self.classes))
                for crop in crops:
                    cropped = crop_image(image, crop)
                    _, raw, e = self.predict(sess, cropped, meta)
                    row_mean += raw
                    if crop == 'no_crop':
                        embedding = e

                row_mean /= len(crops)
                prediction = sess.run(tf.nn.softmax(np.expand_dims(row_mean, 0)))[0]

                similar = self.get_similar(prediction, embedding, similar_count)

                certainties = {k: float(v) for k, v in zip(["1st", "2nd", "3rd", "top3", "top5", "listed"],
                                                    self.certainty_model.get_certainty(row_mean))}
                bests = {}
                for pred, cls in zip(prediction, self.classes):
                    if pred >= threshold:
                        bests[cls] = float(pred)
                return bests, certainties, similar

    def get_similar(self, prediction, embedding, count):
        if count == 0:
            return

        plant_filter = self.embeddings_meta[:, 2] == np.argmax(prediction)
        embeddings = self.embeddings[plant_filter]
        embeddings_meta = self.embeddings_meta[plant_filter]
        embedding = normalize(embedding)
        norms = np.linalg.norm(embeddings - embedding, axis=1)

        return [embeddings_meta[id][4] for id in np.argsort(norms)[:count]]
