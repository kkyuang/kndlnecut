from flask import Flask, Response
import cv2

app = Flask(__name__)

# OpenCV로 웹캠 연결 (0은 기본 웹캠을 의미)
camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        # 웹캠으로부터 프레임 읽기
        success, frame = camera.read()
        if not success:
            break
        else:
            # 좌우 반전
            frame = cv2.flip(frame, 1)  # 1은 좌우 반전, 0은 상하 반전
            # 프레임을 JPEG 포맷으로 인코딩
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            
            # 멀티파트 응답 형태로 프레임 전송
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    # 메인 HTML 페이지
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Webcam Feed</title>
    </head>
    <body>
        <h1>Live Webcam Feed</h1>
        <img src="/video_feed" width="640" height="480">
    </body>
    </html>
    '''

@app.route('/video_feed')
def video_feed():
    # 비디오 스트림 반환
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
