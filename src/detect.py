from flask import Blueprint, request, jsonify
from craft_text_detector import Craft
from src.constants.http_status_codes import HTTP_200_OK
import numpy as np
from PIL import Image
import requests
from math import sqrt, ceil, floor
import pytesseract

detect = Blueprint("detect", __name__, url_prefix="/detect")

craft = Craft(output_dir=None, crop_type="box",
              cuda=False, long_size=1280, link_threshold=0.5, text_threshold=0.7, low_text=0.4)


def boxmerger(data, threshold=10, expand=2):
    results = []

    def convertPointByThreshold(box, thrh):
        [tl, tr, br, bl] = box
        tl = [tl[0] - thrh, tl[1] - thrh]
        tr = [tr[0] + thrh, tr[1] - thrh]
        br = [br[0] + thrh, br[1] + thrh]
        bl = [bl[0] - thrh, bl[1] + thrh]
        return [tl, tr, br, bl]

    def distanceTwoPoints(A, B):
        return sqrt(pow(A[0] - B[0], 2) + pow(A[1] - B[1], 2))

    def VTriangle(I, side):
        [M, N] = side
        # Ax + By + C = 0, I(x, y),
        A = N[1] - M[1]
        B = M[0] - N[0]
        C = M[1] * (N[0] - M[0]) - M[0] * (N[1] - M[1])
        # Distance from a point to a line
        d = abs(A * I[0] + B * I[1] + C) / sqrt(pow(A, 2) + pow(B, 2))
        return d * distanceTwoPoints(M, N) / 2

    def needMerge(resultBox, box, thr):
        [tlthr, trthr, brthr, blthr] = convertPointByThreshold(resultBox, thr)
        VBoxWithThreshold = VBox([tlthr, trthr, brthr, blthr])
        [tl, tr, br, bl] = box
        VBoxNoThreshold = VBox([tl, tr, br, bl])
        hasPointInside = False
        for point in box:
            sumV = VTriangle(point, [tlthr, trthr]) + VTriangle(point, [trthr, brthr]) + \
                VTriangle(point, [brthr, blthr]) + \
                VTriangle(point, [blthr, tlthr])
            if sumV == VBoxWithThreshold:
                hasPointInside = True
                break
        for point in [tlthr, trthr, brthr, blthr]:
            sumV = VTriangle(point, [tl, tr]) + VTriangle(point, [tr, br]) + \
                VTriangle(point, [br, bl]) + VTriangle(point, [bl, tl])
            if sumV == VBoxNoThreshold:
                hasPointInside = True
                break
        return hasPointInside

    def VBox(box):
        [tl, tr, br, bl] = box
        sideVerical = distanceTwoPoints(tl, tr)
        sideHorizontal = distanceTwoPoints(tr, br)
        return sideHorizontal * sideVerical

    def mergebox(resultBox, box):
        [rtl, rtr, rbr, rbl] = resultBox
        [tl, tr, br, bl] = box
        minTop = rtl[1]
        minLeft = min(rtl[0], tl[0])
        maxRight = max(rtr[0], tr[0])
        maxBottom = max(rbr[1], br[1])
        return [[minLeft, minTop], [maxRight, minTop], [maxRight, maxBottom], [minLeft, maxBottom]]

    def normalize(box):
        [tl, tr, br, bl] = box
        top = floor(min(tl[1], tr[1])) - expand
        right = ceil(max(tr[0], br[0])) + expand
        bottom = ceil(max(br[1], bl[1])) + expand
        left = floor(min(tl[0], bl[0])) - expand
        return [[left, top], [right, top], [right, bottom], [left, bottom]]

    for box in data:
        boxNormalized = normalize(box)
        if len(results) == 0:
            results.append(boxNormalized)
        if len(results) > 0:
            for index, res in enumerate(results):
                isMerge = needMerge(res, boxNormalized, threshold)
                if isMerge:
                    results[index] = mergebox(res, boxNormalized)
                    break
                if not (isMerge) and index + 1 == len(results):
                    results.append(boxNormalized)
    return results


class Box:
    def __init__(self, box, text):
        self.box = box
        self.text = text

class Images:
    def __init__(self, url, boxes, lang):
        self.url = url
        self.boxes = boxes
        self.lang = lang


@detect.get('/')
def detect_images():
    images = request.json["images"]
    result = []
    for url in images:
        response = requests.get(url, stream=True)
        np_image = np.array(Image.open(response.raw))
        prediction_result = craft.detect_text(np_image)
        boxes = boxmerger(prediction_result["boxes"].tolist())
        boxMergered = []
        for bbox in boxes:
            [tl, tr, br, bl] = bbox
            crop_img = np_image[tl[1]:br[1], tl[0]:tr[0]]
            box_detected = Box(
                bbox, pytesseract.image_to_string(crop_img, lang="eng"))
            boxMergered.append(box_detected.__dict__)
        img = Images(url, boxMergered, "eng")
        result.append(img.__dict__)

    return jsonify({
        'message': "Image detect successfully!",
        "images": result
    }), HTTP_200_OK
