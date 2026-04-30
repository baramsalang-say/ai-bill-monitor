import requests
import smtplib
import os
from email.mime.text import MIMEText

# [환경 변수]
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def FINAL_DEBUG():
    # 명세서와 이용내역을 고려하여 가장 가능성 높은 주소 2개를 동시에 찔러봅니다.
    urls = [
        "https://open.assembly.go.kr/portal/openapi/ALLBILL",
        "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
    ]
    
    report = "<h3>국회 API 수사 결과 보고</h3>"
    
    for url in urls:
        report += f"<p><b>Target URL:</b> {url}</p>"
        try:
            # 파라미터를 최소화하여 '기본값'으로 호출해봅니다.
            res = requests.get(url, params={'KEY': API_KEY, 'Type': 'json', 'pIndex':1, 'pSize':2}, timeout=20)
            report += f"<pre style='background:#eee; padding:10px;'>{res.text[:1000]}</pre><hr>"
        except Exception as e:
            report += f"<p style='color:red;'>에러: {str(e)}</p><hr>"

    # 결과 메일 발송
    msg = MIMEText(report, 'html')
    msg['Subject'] = "🚨 [긴급] 국회 API 원본 데이터 수사 리포트"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    FINAL_DEBUG()
