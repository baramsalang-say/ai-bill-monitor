import requests
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 환경 변수 세팅
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def fetch_bills_guaranteed():
    url = "https://open.assembly.go.kr/portal/openapi/BILLRCPV2"
    
    # [교정] 범위를 300건으로 늘려 더 많은 데이터를 가져옵니다.
    params = {
        'Key': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 300, 
        'ERACO': '제22대'
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # [테스트용 광범위 키워드] 무엇이라도 걸리게끔 일반적인 단어를 추가했습니다.
        # "법률", "개정", "국가", "정부" 등은 거의 모든 의안에 포함됩니다.
        keywords = [
            "인공지능", "AI", "데이터", "디지털", "소프트웨어", 
            "법률", "개정", "국가", "정부", "조세", "관리"
        ]
        filtered_bills = []

        if 'BILLRCPV2' in data:
            rows = data['BILLRCPV2'][1].get('row', [])
            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                clean_nm = bill_nm.upper().replace(" ", "")
                if any(k.upper() in clean_nm for k in keywords):
                    filtered_bills.append({
                        'date': b.get('PPSL_DT', ''),
                        'title': bill_nm,
                        'proposer': b.get('PPSR_NM', '의원 등'),
                        'link': b.get('LINK_URL', '')
                    })
        return filtered_bills
    except Exception as e:
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🧪 [데이터 확인] 국회 입법 수집 테스트 ({len(bills)}건 발견)"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body style="font-family: 'Malgun Gothic', sans-serif;">
        <h2 style="color: #27ae60;">✅ 시스템 정상 작동 및 데이터 수집 확인</h2>
        <p>광범위 키워드를 적용하여 <b>총 {len(bills)}건</b>의 데이터를 수집했습니다.</p>
    """
    if not bills:
        html += "<p style='color: red;'>여전히 0건이라면 API 승인 상태를 확인해야 합니다.</p>"
    else:
        html += "<table border='1' style='border-collapse: collapse; width: 100%; border-color: #ddd;'>"
        html += "<tr style='background:#f4f4f4;'><th>접수일</th><th>의안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:8px; text-align:center;'>{b['date']}</td><td style='padding:8px;'><a href='{b['link']}'>{b['title']}</a></td><td style='padding:8px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    html += "</body></html>"

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    results = fetch_bills_guaranteed()
    send_email(results)
