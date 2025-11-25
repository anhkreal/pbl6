from flask import Flask, Response, jsonify, request, render_template
from camera import Camera
from log_batcher import EmotionLogBatcher
import time

app = Flask(__name__)
camera = Camera()
log_batcher = EmotionLogBatcher(post_interval=5.0)  # seconds

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video_stream():
    def generate():
        for frame_jpeg, meta in camera.frames():
            # enqueue negative emotions for batching
            if meta.get('emotion') and meta.get('emotion_type') == 'negative':
                log_batcher.enqueue(meta)
            boundary = '--frame\r\nContent-Type: image/jpeg\r\n\r\n'
            yield boundary + frame_jpeg + '\r\n'
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def stats():
    return jsonify(camera.last_meta())

@app.route('/flush-logs', methods=['POST'])
def flush_logs():
    # force flush (debug)
    sent = log_batcher.flush()
    return jsonify({'sent': sent})

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
    finally:
        camera.release()
