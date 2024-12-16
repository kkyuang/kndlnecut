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
    img.save(f"qr_{hash_value}.png")

    return {
        "folder_name": folder_name,
        "hash": hash_value,
        "qr_url": qr_url,
        "qr_image": f"qr_{hash_value}.png"
    }

# 테스트 실행
if __name__ == "__main__":
    folder_name = "202412160650"  # 예제 폴더 이름
    result = generate_qr(folder_name)

    print("폴더 이름:", result["folder_name"])
    print("해시 값:", result["hash"])
    print("QR 코드 URL:", result["qr_url"])
    print("QR 코드 이미지 파일:", result["qr_image"])
