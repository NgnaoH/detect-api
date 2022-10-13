from flask import Blueprint, request, jsonify
from craft_text_detector import Craft
from src.constants.http_status_codes import HTTP_200_OK
import numpy as np
from PIL import Image
import requests

detect = Blueprint("detect", __name__, url_prefix="/api/v1/detect")

long_size = 1280
craft = Craft(output_dir=None, crop_type="box",
              cuda=False, long_size=long_size)


class Images:
    def __init__(self, url, boxes):
        self.url = url
        self.boxes = boxes
        self.size = long_size

@detect.get('/')
def detect_images():
    images = request.json["images"]

    result = []
    for url in images:
        response = requests.get(url, stream=True)
        image = np.array(Image.open(response.raw))
        prediction_result = craft.detect_text(image)
        boxes = prediction_result["boxes"].tolist()
        print(prediction_result)
        img = Images(url, boxes)
        result.append(img.__dict__)

    return jsonify({
        'message': "Image detect successfully!",
        "images": result
    }), HTTP_200_OK
