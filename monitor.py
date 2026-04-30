import requests
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [환경 변수] GitHub Secrets 설정을 꼭 확인하세요.
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def fetch_all_bills_test():
    # 명세서(image_2ac3ff.png) 기준 BILLRCPV2 주소
    url = "https://open.assembly.go.kr/portal/openapi/BILLRCPV2"
    
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 10  # 가장 최근에 접수된 딱 10건만 가져옵니다.
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        all_bills = []
        if 'BILLRCPV2' in data:
            rows = data['BILLRCPV2'][1].get('row', [])
            for b in rows:
                all_bills.append({
                    'date': b.get('PPSL_DT', ''),
                    'title': b.get('BILL_NM', ''),
                    'proposer': b.get('PPSR_NM', '의원 등'),
                    'link': b.get('LINK_URL', '')
                })
        return all_bills
    except Exception as e:
        print(f"테스트 호출 에러: {e}")
        return []

def send_test_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🚀 [최종 테스트] 국회 최신 접수 데이터 {len(bills)}건 수신 성공"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body>
        <h2 style="color: #27ae60;">✅ 시스템 최종 수신 테스트</h2>
        <p>키워드 필터링을 해제하고 <b>국회 서버에서 온 생생한 최신 10건</b>을 그대로 보여줍니다.</p>
    """
    if not bills:
        html += "<p style='color: red;'>데이터가 한 건도 없습니다. API 승인 상태나 키 값을 다시 확인해야 합니다.</p>"
    else:
        html += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        html += "<tr style='background:#f4f4f4;'><th>접수일</th><th>의안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:8px;'>{b['date']}</td><td style='padding:8px;'>{b['title']}</td><td style='padding:8px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    html += "</body></html>"

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    results = fetch_all_bills_test()
    send_test_email(results)
