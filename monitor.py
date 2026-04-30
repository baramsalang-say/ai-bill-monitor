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

def fetch_bills():
    # 가장 확실한 의안목록전체 주소 (v2 타겟)
    url = "https://open.assembly.go.kr/portal/openapi/nzmimehqvxbmqvpif"
    
    # 진단을 위해 1,000건을 한꺼번에 가져옵니다.
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 1000 
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        all_recent_samples = [] # 샘플 확인용
        filtered_bills = []
        
        keywords = ["인공지능", "AI", "데이터", "지능", "디지털", "소프트웨어", "정보통신", "ICT", "플랫폼"]
        
        if 'nzmimehqvxbmqvpif' in data:
            rows = data['nzmimehqvxbmqvpif'][1].get('row', [])
            
            # 상위 5개를 샘플로 저장
            for i in range(min(5, len(rows))):
                all_recent_samples.append(rows[i].get('BILL_NM', '의안명 없음'))

            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                clean_nm = bill_nm.upper().replace(" ", "")
                if any(k.upper() in clean_nm for k in keywords):
                    filtered_bills.append({
                        'date': b.get('PROPOSE_DT', ''),
                        'title': bill_nm,
                        'proposer': b.get('PROPOSER', ''),
                        'link': f"https://likms.assembly.go.kr/bill/billDetail.do?billId={b.get('BILL_ID')}"
                    })
        return filtered_bills, all_recent_samples
    except Exception as e:
        print(f"에러: {e}")
        return [], [str(e)]

def send_email(bills, samples):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [데이터 진단] 국회 입법 모니터링 ({len(bills)}건 발견)"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body>
        <h3>1. 키워드 필터링 결과: {len(bills)}건</h3>
    """
    if bills:
        html += "<table border='1'><tr><th>날짜</th><th>의안명</th></tr>"
        for b in bills:
            html += f"<tr><td>{b['date']}</td><td><a href='{b['link']}'>{b['title']}</a></td></tr>"
        html += "</table>"
    else:
        html += "<p style='color:red;'>선택하신 키워드와 일치하는 법안이 최신 1,000건 중에는 없습니다.</p>"

    html += f"""
        <br><hr>
        <h3>2. 시스템이 실제로 가져온 최신 법안 샘플 (Top 5)</h3>
        <p>아래 목록이 보인다면 API 연결은 완벽한 것입니다.</p>
        <ul>
    """
    for s in samples:
        html += f"<li>{s}</li>"
    html += "</ul></body></html>"

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    bills, samples = fetch_bills()
    send_email(bills, samples)
