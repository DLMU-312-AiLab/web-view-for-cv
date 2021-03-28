from flask import Flask, render_template, request, make_response
from werkzeug.utils import secure_filename
import os
import datetime
import uuid
import json
import sys


app = Flask(__name__)
config = dict()


def public_url(path):
    return config["hostname"] + path


def ajax_json(code, message):
    data = dict()
    data["code"] = code
    data["message"] = message
    return json.dumps(data)


def gen_dir():
    os.chdir(config["web_root"])
    basename = datetime.datetime.now().strftime("%Y-%m-%d")
    local_path = os.path.join(config["upload_path"], basename)
    if not os.path.exists(local_path):
        os.mkdir(local_path)
    return local_path


def gen_file_name_and_path(local_path, filename):
    prefix = str(uuid.uuid1())
    suffix = secure_filename(filename).split(".")[-1]
    return os.path.join(local_path, "%s.%s" % (prefix, suffix))


@app.route('/check_ajax', methods=['POST'])
def check_ajax():
    if request.method == 'POST':
        data = request.get_data()
        json_data = json.loads(data.decode("utf-8"))
        file_name = json_data.get("file_name")
        import ocr
        return ajax_json(0, ocr.image_run(file_name))


@app.route('/upload_ajax', methods=['GET', 'POST'])
def uploader():
    if request.method == 'POST':
        f = request.files['file']
        filepath = gen_file_name_and_path(gen_dir(), f.filename)
        f.save(filepath)
        f.close()

        data = dict()
        data["public_url"] = public_url(filepath)
        data["file_name"] = filepath
        return ajax_json(0, data)


@app.route('/upload/<string:path>/<string:filename>', methods=['GET'])
def display_img(path, filename):
    if request.method == 'GET':
        if filename is None or path is None:
            pass
        else:
            image_data = open(os.path.join(config["upload_path"], path, filename), "rb").read()
            response = make_response(image_data)
            response.headers['Content-Type'] = 'image/jpg'
            return response


@app.route('/upload_view')
def upload_file():
    return render_template('./upload_view.html',
                           upload_url=config["upload_url"],
                           check_ajax=config['check_ajax'])


@app.route('/')
def index():
    return upload_file()


def init():
    config["hostname"] = "http://%s:%s/" % (sys.argv[1], sys.argv[2])
    config["upload_path"] = "upload/"
    config["web_root"] = os.getcwd()
    config["upload_url"] = config["hostname"] + "upload_ajax"
    config["check_ajax"] = config["hostname"] + "check_ajax"
    app.config['UPLOAD_FOLDER'] = config["upload_path"]


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("python ./%s <public_ip> <port>" % sys.argv[0])
        sys.exit(1)
    init()
    app.run(host="0.0.0.0", port=sys.argv[2], debug=True)
