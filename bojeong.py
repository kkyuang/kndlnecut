import cv2
import numpy as np
from PIL import Image, ImageFilter

# 1. 얼굴 탐지
def detect_faces(image_path):
    # 이미지 읽기
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Haar Cascade 얼굴 탐지기 로드
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # 얼굴 탐지
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    return faces, image

# 2. 피부톤 보정
def correct_skin_tone(image, faces):
    for (x, y, w, h) in faces:
        # 얼굴 부분만 추출
        face = image[y:y+h, x:x+w]

        # 피부 톤을 일정하게 맞추는 간단한 방법 (예: 피부톤 밝기 조정)
        hsv = cv2.cvtColor(face, cv2.COLOR_BGR2HSV)
        hsv[..., 1] = 255  # 채도를 255로 고정시켜서 피부색을 일정하게 만듬
        adjusted_face = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        # 얼굴에 피부 톤 조정된 이미지를 덮어씌우기
        image[y:y+h, x:x+w] = adjusted_face
    
    return image

# 3. 잡티 제거
def remove_spots(image, faces):
    for (x, y, w, h) in faces:
        # 얼굴 부분만 추출
        face = image[y:y+h, x:x+w]

        # 얼굴의 잡티를 블러 처리하여 제거 (예: medianBlur 사용)
        face_blurred = cv2.medianBlur(face, 15)  # 커널 크기 조정으로 블러 효과 조절

        # 얼굴에 블러 처리된 이미지를 덮어씌우기
        image[y:y+h, x:x+w] = face_blurred

    return image

# 주 함수: 이미지 처리 및 얼굴 보정
def process_image(image_path):
    faces, image = detect_faces(image_path)
    if len(faces) == 0:
        print("얼굴을 찾을 수 없습니다.")
        return None

    # 피부톤 보정
    image = correct_skin_tone(image, faces)

    # 잡티 제거
    image = remove_spots(image, faces)

    # 결과 이미지 저장
    result_image_path = "processed_" + image_path.split('/')[-1]
    cv2.imwrite(result_image_path, image)
    
    # 결과 이미지 보기

    return result_image_path

# 사용 예시
image_path = 'face.jpg'
processed_image = process_image(image_path)
print(f"처리된 이미지는 {processed_image}에 저장되었습니다.")
