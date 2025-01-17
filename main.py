from flask import Flask, send_from_directory, render_template, Response, request, redirect, url_for, send_file, jsonify
import cv2
import os
import win32print
import win32ui
import json
from PIL import Image, ImageDraw, ImageWin, ImageFont
import time
import subprocess
from datetime import datetime

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
def get_background(filename):
    return send_from_directory(app.config['background'], filename)


# 경로 설정
NOWIMGS_DIR = os.path.join(os.getcwd(), 'nowimgs')
FRAME_INFO_FILE = os.path.join(os.getcwd(), 'frameinfo.json')
FRAME_IMAGE = os.path.join(os.getcwd(), 'decorations/frame')

def resize_and_crop(img, target_width, target_height):
    """
    이미지 비율을 유지하며 리사이징 후, 중앙 기준으로 (target_width, target_height)에 정확히 맞게 크롭합니다.
    """
    # 원본 이미지 크기
    img_width, img_height = img.size

    # 목표 영역 비율
    target_ratio = target_width / target_height
    img_ratio = img_width / img_height

    if img_ratio > target_ratio:
        # 이미지가 더 넓은 경우: 높이를 기준으로 리사이즈
        new_height = target_height
        new_width = int(target_height * img_ratio)
    else:
        # 이미지가 더 높은 경우: 너비를 기준으로 리사이즈
        new_width = target_width
        new_height = int(target_width / img_ratio)

    # 리사이즈 수행 (비율 유지)
    img = img.resize((new_width, new_height), Image.LANCZOS)

    # 중앙 기준 크롭 (목표 영역 w, h와 정확히 일치하도록)
    left = (new_width - target_width) / 2
    top = (new_height - target_height) / 2
    right = (new_width + target_width) / 2
    bottom = (new_height + target_height) / 2

    # 이미지 크롭
    cropped_img = img.crop((left, top, right, bottom))

    # 크롭된 이미지의 최종 크기 확인 및 강제 조정
    cropped_img = cropped_img.resize((target_width, target_height), Image.LANCZOS)

    return cropped_img

import hashlib
import qrcode

def create_hash(folder_name):
    """
    SHA256 해시 생성 후 10자리로 자르기
    """
    hash_object = hashlib.sha256(folder_name.encode())
    return hash_object.hexdigest()[:10]  # 해시값의 첫 10자리만 사용

def generate_qr(folder_name, domain="https://kndl4cut.toby2718.com"):
    """
    QR 코드 URL 생성 및 출력
    """
    # 해시 처리된 폴더 이름 생성
    hash_value = create_hash(folder_name)

    # QR 코드 링크 생성
    qr_url = f"{domain}/photo/{hash_value}"

    # QR 코드 생성
    qr = qrcode.QRCode(
        version=1,  # QR 코드 크기 (1 ~ 40)
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)

    # QR 코드 이미지 생성 및 저장
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"nowimgs/resultQR.png")

    return {
        "folder_name": folder_name,
        "hash": hash_value,
        "qr_url": qr_url,
        "qr_image": f"qr_{hash_value}.png"
    }


@app.route('/generate_result/<framename>')
def generate_result(framename):
    # 1. frameinfo.json 파일에서 좌표 읽기
    with open(FRAME_INFO_FILE, 'r') as f:
        frame_info = json.load(f)

    # 현재 날짜, 시간, 분을 형식에 맞게 가져옵니다
    current_time = datetime.now().strftime('%Y%m%d%H%M')
    generate_qr(current_time )

    # 2. 선택된 프레임 이미지와 좌표 확인
    if framename not in frame_info:
        return f"Error: {framename} not found in frameinfo.json", 404
    
    frame_image_path = os.path.join(FRAME_IMAGE, framename)
    if not os.path.exists(frame_image_path):
        return f"Error: Frame image '{framename}' not found", 404

    # 2. 프레임 이미지 불러오기
    frame_img = Image.open(frame_image_path).convert("RGBA")

    # 3. 촬영된 네 장의 사진 불러오기
    photos = [
        os.path.join(NOWIMGS_DIR, f"{i}.jpg") for i in range(4)
    ]
    
    
    photo = Image.open('nowimgs/resultQR.png')
    photo2 = resize_and_crop(photo, 120, 120)
    frame_img.paste(photo2, (1060, 1660), photo2.convert("RGBA"))

    # 4. 사진을 프레임에 순서대로 합성
    for idx, coords in enumerate(frame_info[framename]):
        x, y, w, h = coords
        if idx >= len(photos):
            break
        photo = Image.open(photos[idx])

        # 중앙 기준 비율 유지 리사이징 및 크롭
        photo2 = resize_and_crop(photo, w, h)

        frame_img.paste(photo2, (x, y), photo2.convert("RGBA"))

    # 5. 결과 이미지 저장
    result_path = os.path.join(NOWIMGS_DIR, 'result.png')
    frame_img.save(result_path)

    # 폴더 경로 설정
    folder_path = os.path.join('Z:\\cutbooth\\photos', current_time)

    # 폴더 생성
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        frame_img.save(os.path.join(folder_path, 'result.png'))

    frame_img.save(result_path)
    return redirect(url_for('print_page'))



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


@app.route('/photo_shoot')
def photo_shoot():
    # 1. frameinfo.json 파일에서 좌표 읽기
    frame_info={}
    with open(FRAME_INFO_FILE, 'r') as f:
        frame_info = json.load(f)

    return render_template('photo_shoot.html', aspect_ratios=frame_info)


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

            #얼굴보정 

            command = ["python", "infer.py", "--input", "../" + filename]
            working_directory = "face-smoothing"

            # 명령 실행
           # process = subprocess.Popen(command, cwd=working_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


            return jsonify({"status": "success", "photo_index": photo_index})
    return jsonify({"status": "error", "message": "Failed to capture photo."})

@app.route('/print_page')
def print_page():
    global captured_images, selected_frame
    price = len(captured_images) * 1000
    return render_template('print_page.html', images=captured_images, frame=selected_frame, price=price)





NOWIMGS_DIR = os.path.join(os.getcwd(), 'nowimgs')
RESULT_IMAGE_PATH = os.path.join(NOWIMGS_DIR, 'result.png')



@app.route('/print_photo', methods=['POST'])
def print_photo():
    count = int(request.form.get('count', 1))  # 인화 장수
    if not os.path.exists(RESULT_IMAGE_PATH):
        return "Error: Result image not found", 404

    try:
        print_image_to_printer(RESULT_IMAGE_PATH, count)  # 프린터로 출력
        return redirect('/')
        
    except Exception as e:
        return f"Printing failed: {e}", 500
    



def print_image_to_printer(image_path, n):
    """
    Windows 프린터로 이미지를 여백 없이 꽉 차게 출력하는 함수
    """
    # 프린터 설정
    printer_name = 'Brother MFC-T920DW'  # 프린터 이름
    hprinter = win32print.OpenPrinter(printer_name)
    printer_info = win32print.GetPrinter(hprinter, 2)

    hdc_printer = win32ui.CreateDC()
    hdc_printer.CreatePrinterDC(printer_name)

    # 프린터 출력 영역 크기 가져오기
    printer_width = hdc_printer.GetDeviceCaps(110)  # HORZRES: 가로 해상도
    printer_height = hdc_printer.GetDeviceCaps(111)  # VERTRES: 세로 해상도

    # 이미지 불러오기
    img = Image.open(image_path)
    img_width, img_height = img.size

    # 이미지 비율 조정 (여백 없이 꽉 차게 맞춤)
    img_ratio = img_width / img_height
    printer_ratio = printer_width / printer_height

    if img_ratio > printer_ratio:
        # 이미지가 더 넓은 경우 -> 높이를 기준으로 잘라냄
        new_width = int(img_height * printer_ratio)
        offset = (img_width - new_width) // 2
        crop_box = (offset, 0, offset + new_width, img_height)
    else:
        # 이미지가 더 긴 경우 -> 너비를 기준으로 잘라냄
        new_height = int(img_width / printer_ratio)
        offset = (img_height - new_height) // 2
        crop_box = (0, offset, img_width, offset + new_height)

    img_cropped = img.crop(crop_box)

    # 이미지 크기를 프린터 해상도에 맞춤
    img_resized = img_cropped.resize((printer_width, printer_height), Image.LANCZOS)

    for _ in range(n):
        # 출력 시작
        hdc_printer.StartDoc("Image Print")
        hdc_printer.StartPage()

        # Pillow의 ImageWin으로 프린터에 이미지 출력
        dib = ImageWin.Dib(img_resized)
        dib.draw(hdc_printer.GetHandleOutput(), (0, 0, printer_width-120, printer_height-160))

        # 출력 종료
        hdc_printer.EndPage()
        hdc_printer.EndDoc()
    hdc_printer.DeleteDC()
    win32print.ClosePrinter(hprinter)


if __name__ == '__main__':
    app.run(debug=True)
