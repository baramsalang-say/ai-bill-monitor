import requests
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [환경 변수] GitHub Secrets에 등록된 값을 사용합니다.
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def fetch_bills():
    # [교정] 신청하신 서비스 명칭에 맞춰 V2를 제거한 BILLRCP 주소를 사용합니다.
    url = "https://open.assembly.go.kr/portal/openapi/BILLRCP"
    
    params = {
        'Key': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 300  # 검색 범위를 최근 300건으로 확대
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # [테스트] 데이터 수집 확인을 위해 범용 키워드를 포함했습니다.
        # 나중에 안정화되면 "법률", "개정" 등은 삭제하셔도 됩니다.
        keywords = [
            "인공지능", "AI", "데이터", "지능정보", "디지털", "소프트웨어", 
            "법률", "개정", "국가", "정보", "통신"
        ]
        filtered_bills = []

        # [교정] 응답 구조에서도 V2를 제거하여 BILLRCP로 접근합니다.
        if 'BILLRCP' in data:
            rows = data['BILLRCP'][1].get('row', [])
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
        return filtered_bills, data
    except Exception as e:
        return [], {"error": str(e)}

def send_email(bills, raw_log):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [최종확인] 국회 입법 수집 리포트 ({len(bills)}건 발견)"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body style="font-family: 'Malgun Gothic', sans-serif;">
        <h2 style="color: #002d56;">📊 NIA 지능정보사회 입법 모니터링</h2>
        <p>서비스 규격(BILLRCP) 교정 후 <b>최근 300건</b>의 의안을 분석한 결과입니다.</p>
    """
    
    if not bills:
        html += f"""
        <p style='color: #e74c3c; font-weight: bold;'>데이터가 발견되지 않았습니다.</p>
        <p style='font-size: 12px; color: #666;'>서버 응답 로그: {raw_log}</p>
        """
    else:
        html += f"<p>총 <b>{len(bills)}건</b>의 의안이 감지되었습니다.</p>"
        html += "<table border='1' style='border-collapse: collapse; width: 100%; border-color: #ddd;'>"
        html += "<tr style='background:#f8f9fa;'><th>접수일</th><th>의안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:8px; text-align:center;'>{b['date']}</td><td style='padding:8px;'><a href='{b['link']}' style='font-weight:bold; color:#002d56;'>{b['title']}</a></td><td style='padding:8px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    
    html += "</body></html>"
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    results, log = fetch_bills()
    send_email(results, log)
