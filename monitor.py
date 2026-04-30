import requests
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [환경 변수]
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def fetch_debug_info():
    # v2 전용 주소
    url = "https://open.assembly.go.kr/portal/openapi/nzmimehqvxbmqvpif"
    params = { 'KEY': API_KEY, 'Type': 'json', 'pIndex': 1, 'pSize': 3 }

    try:
        response = requests.get(url, params=params, timeout=30)
        # 서버 응답 텍스트 전체를 가져옵니다.
        raw_text = response.text
        return raw_text
    except Exception as e:
        return f"통신 에러 발생: {str(e)}"

def send_debug_email(raw_content):
    msg = MIMEMultipart()
    msg['Subject'] = f"🚨 [긴급진단] 국회 API 서버 응답 전문 ({datetime.now().strftime('%H:%M')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    body = f"""
    <h3>국회 서버에서 보내온 실제 데이터(Raw Text)입니다.</h3>
    <p>아래 박스 안의 내용을 그대로 복사해서 저에게 알려주세요.</p>
    <div style="background: #f4f4f4; padding: 15px; border: 1px solid #ccc; font-family: monospace; white-space: pre-wrap;">
    {raw_content}
    </div>
    """
    msg.attach(MIMEText(body, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    debug_data = fetch_debug_info()
    send_debug_email(debug_data)
