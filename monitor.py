import requests
import smtplib
import os
from email.mime.text import MIMEText

API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def LAST_CHANCE_CHECK():
    # 명세서(image_2ac3ff.png)와 100% 일치하는 파라미터 조합
    url = "https://open.assembly.go.kr/portal/openapi/BILLRCPV2"
    params = {'KEY': API_KEY, 'Type': 'json', 'pIndex': 1, 'pSize': 5}
    
    try:
        res = requests.get(url, params=params, timeout=20)
        json_data = res.json()
        
        # 성공/실패 여부를 불문하고 서버 응답 전문을 메일로 발송
        body = f"<h3>서버 응답 결과</h3><pre>{res.text}</pre>"
        
        msg = MIMEText(body, 'html')
        msg['Subject'] = "🚨 국회 API 최종 응답 수사 리포트"
        msg['From'] = MY_EMAIL
        msg['To'] = RECEIVE_EMAIL

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MY_EMAIL, EMAIL_PW)
            server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
    except Exception as e:
        print(f"통신 에러: {e}")

if __name__ == "__main__":
    LAST_CHANCE_CHECK()
