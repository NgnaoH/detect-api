from flask import Blueprint, jsonify
from src.constants.http_status_codes import HTTP_200_OK
import pytesseract

languages = Blueprint("languages", __name__, url_prefix="/languages")

@languages.get('/')
def get_languages():
    languages = pytesseract.get_languages()

    return jsonify({
        'message': "Get languages successfully!",
        "languages": languages,
    }), HTTP_200_OK
