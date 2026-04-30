import smtplib
from email.mime.text import MIMEText
import os

# Secrets 설정값 가져오기
MY_EMAIL = "baramsalang@gmail.com"
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def simple_test():
    try:
        msg = MIMEText("시스템 통신 테스트입니다. 이 메일이 보이면 성공입니다.")
        msg['Subject'] = "🔔 [GitHub Actions] 최종 연결 확인"
        msg['From'] = MY_EMAIL
        msg['To'] = RECEIVE_EMAIL

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MY_EMAIL, EMAIL_PW)
            server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
        print("메일 발송 성공!")
    except Exception as e:
        print(f"메일 발송 실패: {e}")

if __name__ == "__main__":
    simple_test()
