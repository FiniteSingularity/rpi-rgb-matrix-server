from flask import Flask, request
from flask_cors import CORS
from celery import Celery
import time
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from utils import process_data

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['result_backend'],
        broker=app.config['CELERY_BROKER_URL'],
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


flask_app = Flask(__name__)

flask_app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    result_backend='redis://localhost:6379'
)

CORS(flask_app)

celery = make_celery(flask_app)


@celery.task()
def scroll_twitch_message(data, num_passes = 2):
    images, text = process_data(data)

    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 64
    options.chain_length = 2
    options.parallel = 1
    options.drop_privileges = 0
    options.daemon = 0

    matrix = RGBMatrix(options = options)
    double_buffer = matrix.CreateFrameCanvas()
    
    x_offset = 129
    last_x_change = 0
    current_pass = 0

    x_t_length = 16

    while current_pass < num_passes:
        message_width = 0
        double_buffer.Clear()
        current_time = int(round(time.time() * 1000))
        dt = current_time - last_x_change

        if dt > x_t_length:
            dx = -1
            last_x_change = current_time
        else:
            dx = 0

        for id, value in images.items():
            current_frame = value["current_frame"]
            dt = current_time - value["current_frame_start"]

            max_dt = value["frames"][current_frame]["duration"]
            if dt > max_dt:
                value["current_frame"] = (value["current_frame"] + 1) % len(value["frames"])
                value["current_frame_start"] = current_time

        for index, entity in enumerate(data):
            if entity["mc_type"] == "string":
                frames = text[index]
                for frame in frames:
                    w, h = frame.size
                    y_offset = 1
                    double_buffer.SetImage(frame, message_width + x_offset, y_offset)
                    message_width += w
            else:
                frames = images[entity["value"]]["frames"]
                current_frame = images[entity["value"]]["current_frame"]
                frame = frames[current_frame]["frame"]
                double_buffer.SetImage(frame, x_offset + message_width + 2, 2)
                message_width += 32

        double_buffer = matrix.SwapOnVSync(double_buffer)

        x_offset += dx
        if x_offset < -message_width:
            x_offset = 128
            current_pass += 1


@flask_app.route("/", methods = ['POST'])
def index():
    data = request.get_json(force=True)
    result = scroll_twitch_message.delay(data, 2)
    return '{"submitted": true}'

