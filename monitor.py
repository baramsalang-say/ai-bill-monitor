import requests
import smtplib
import os
from email.mime.text import MIMEText

API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def FORCE_CHECK():
    url = "https://open.assembly.go.kr/portal/openapi/BILLRCPV2"
    # 모든 조건을 빼고 가장 생생한 데이터 1건만 요청
    params = {'KEY': API_KEY, 'Type': 'json', 'pIndex': 1, 'pSize': 1}
    
    try:
        res = requests.get(url, params=params, timeout=20)
        raw_data = res.text # 서버가 준 가공되지 않은 텍스트
        
        msg = MIMEText(f"<h3>국회 서버 응답 전문:</h3><pre>{raw_data}</pre>", 'html')
        msg['Subject'] = "🚨 [최종확인] 국회 API 원본 응답 테스트"
        msg['From'] = MY_EMAIL
        msg['To'] = RECEIVE_EMAIL

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MY_EMAIL, EMAIL_PW)
            server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
    except Exception as e:
        print(f"통신 자체 실패: {e}")

if __name__ == "__main__":
    FORCE_CHECK()
