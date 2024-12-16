from flask import Flask, send_from_directory, render_template, Response, request, redirect, url_for, send_file, jsonify
import cv2
import os
from PIL import Image, ImageDraw, ImageFont
import time

app = Flask(__name__)

# 웹캠 연결
camera = cv2.VideoCapture(0)
frame_folder = "./decorations/frame"
background_folder = "./decorations/background"
output_folder = "./nowimgs"
os.makedirs(output_folder, exist_ok=True)
captured_images = []  # 사진 저장 리스트
selected_frame = None

# 파일이 저장된 폴더 경로
app.config['nowimgs'] = 'nowimgs'
app.config['frame'] = 'decorations/frame'
app.config['background'] = 'decorations/background'

# 파일 제공 경로 설정 - 현재 촬영된 이미지
@app.route('/nowimgs/<filename>')
def get_nowimgs(filename):
    return send_from_directory(app.config['nowimgs'], filename)

# 파일 제공 경로 설정 - 프레임
@app.route('/frame/<filename>')
def get_frame(filename):
    return send_from_directory(app.config['frame'], filename)

# 파일 제공 경로 설정 - 배경
@app.route('/background/<filename>')
def get_backgrounds(filename):
    return send_from_directory(app.config['background'], filename)

# 웹캠 프레임 전달 함수
def generate_webcam():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # 좌우 반전
            frame = cv2.flip(frame, 1)  # 1은 좌우 반전, 0은 상하 반전
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def start_page():
    return render_template('start.html')

@app.route('/frame_select')
def frame_select():
    frames = os.listdir(frame_folder)
    backgrounds = os.listdir(background_folder)
    return render_template('frame_select.html', frames=frames, backgrounds=backgrounds)

@app.route('/select_frame', methods=['POST'])
def select_frame():
    global selected_frame
    selected_frame = request.form['frame']
    return redirect(url_for('photo_shoot'))

@app.route('/photo_shoot')
def photo_shoot():
    return render_template('photo_shoot.html')


@app.route('/video_feed')
def video_feed():
    # photo_shoot.html에서만 웹캠을 제공
    if request.referrer and "photo_shoot" in request.referrer:
        return Response(generate_webcam(), mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Forbidden", 403

@app.route('/take_photo', methods=['POST'])
def take_photo():
    data = request.get_json()
    photo_index = data.get('photo_index')
    
    if photo_index is not None:
        success, frame = camera.read()
        if success:
            filename = os.path.join(output_folder, f"{photo_index}.jpg")
            cv2.imwrite(filename, frame)  # 이미지 저장
            return jsonify({"status": "success", "photo_index": photo_index})
    return jsonify({"status": "error", "message": "Failed to capture photo."})

@app.route('/print_page')
def print_page():
    global captured_images, selected_frame
    price = len(captured_images) * 1000
    return render_template('print_page.html', images=captured_images, frame=selected_frame, price=price)

@app.route('/print_photo', methods=['POST'])
def print_photo():
    count = int(request.form['count'])
    price = count * 1000
    output_path = "static/final_print.jpg"
    
    # 사진 합성 (프레임과 사진 3장)
    frame_img = Image.open(os.path.join(frame_folder, selected_frame)).convert("RGBA")
    for idx, img_path in enumerate(captured_images):
        photo = Image.open(img_path).resize((200, 200))  # 임의 사이즈 조절
        frame_img.paste(photo, (100, 100 + idx * 210), photo)
    
    frame_img.save(output_path)
    for _ in range(count):
        os.system(f"lp {output_path}")  # 프린터 출력 (리눅스 기준)
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
