import base64
from dataclasses import dataclass
from hashlib import md5
from io import BytesIO

from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image

app = Flask(__name__)
CORS(app)


@app.errorhandler(400)
def bad_request(e):
    return jsonify(code=400, msg="请求报文存在语法错误"), 400


@app.errorhandler(404)
def page_not_found(e):
    return jsonify(code=404, msg="找不到此资源"), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify(code=405, msg="方法不被允许"), 405


@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(code=500, msg="服务器内部错误"), 500


@app.errorhandler(Exception)
def the_api_error(e):
    if isinstance(e, APIError):
        return jsonify(code=e.code, msg=e.message)


@dataclass
class APIError(Exception):
    message: str
    code: int = 500


def get_request_body(*keys) -> list:
    try:
        value = []
        data = request.get_json()
        for key in keys: value.append(data[key])
    except (KeyError, TypeError):
        raise APIError("缺少参数")
    else:
        return value


def upper_md5(s: str) -> str:
    if not isinstance(s, bytes): s = bytes(s, encoding='utf-8')
    return md5(s).hexdigest().upper()


def make_even_image(image):
    image = image.convert('RGBA')
    image_blender = Image.new('RGBA', image.size, (0, 0, 0, 0))
    image = Image.blend(image_blender, image, 1)

    pixels = [(r >> 1 << 1, g >> 1 << 1, b >> 1 << 1, a >> 1 << 1)
              for r, g, b, a in image.getdata()]

    even_image = Image.new(image.mode, image.size)
    even_image.putdata(pixels)
    return even_image


def encode_data_in_image(image, data):
    def int_to_binary_str(i):
        return '0' * (8 - len(bin(i)[2:])) + bin(i)[2:]

    even_image = make_even_image(image)

    binary = ''.join(map(int_to_binary_str, bytearray(data, 'utf-8')))

    if len(binary) > len(even_image.getdata()) * 4:
        raise APIError(message="图片容不下加密文本")

    encoded_pixels = [(r + int(binary[index * 4 + 0]),
                       g + int(binary[index * 4 + 1]),
                       b + int(binary[index * 4 + 2]),
                       t + int(binary[index * 4 + 3]))
                      if index * 4 < len(binary) else (r, g, b, t)
                      for index, (r, g, b, t) in enumerate(even_image.getdata())]

    encoded_image = Image.new(even_image.mode, even_image.size)
    encoded_image.putdata(encoded_pixels)
    return encoded_image


def decode_data_from_image(image):
    binary = ''.join([bin(r)[-1] + bin(g)[-1] + bin(b)[-1] + bin(a)[-1]
                      for r, g, b, a in image.getdata()])

    many_zero_index = binary.find('0' * 16)

    end_index = (many_zero_index + 8 - many_zero_index % 8
                 if many_zero_index % 8 != 0 else many_zero_index)
    data = binary_to_string(binary[:end_index])
    return data


def binary_to_string(binary):
    index = 0
    strings = []

    def effective_binary(binary_part, zero_index):
        if not zero_index:
            return binary_part[1:]
        binary_list = []
        for i in range(zero_index):
            small_part = binary_part[8 * i: 8 * i + 8]
            binary_list.append(small_part[small_part.find('0') + 1:])
        return ''.join(binary_list)

    while index + 1 < len(binary):
        zero_index_1 = binary[index:].index('0')
        length = zero_index_1 * 8 if zero_index_1 else 8
        string = chr(int(effective_binary(
            binary[index: index + length], zero_index_1), 2))
        strings.append(string)
        index += length

    return ''.join(strings)


@app.route('/encode', methods=("POST",))
def api_encode_data_in_image():
    img, msg = get_request_body("img", "msg")

    img_data = img.split(",")[1]
    img_io = base64.b64decode(img_data)
    image = Image.open(BytesIO(img_io))

    uri = f"./static/{upper_md5(img_data + msg)}.png"
    new_image = encode_data_in_image(image, msg)
    new_image.save(uri)

    return jsonify(code=200, msg="ok", imgUrl=f"{request.host_url}{uri[2:]}")


@app.route('/decode', methods=("POST",))
def api_decode_data_from_image():
    img = get_request_body("img")[0]

    img_data = img.split(",")[1]
    img_io = base64.b64decode(img_data)
    image = Image.open(BytesIO(img_io))

    return jsonify(code=200, msg=decode_data_from_image(image))
