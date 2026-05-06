import requests
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [환경 변수]
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

# 모니터링 키워드 리스트 (메일 본문에 표시하기 위해 변수로 분리)
MONITORING_KEYWORDS = [
    "인공지능", "AI", "데이터", "디지털", "지능정보", "ICT", "정보통신", 
    "플랫폼", "알고리즘", "클라우드", "소프트웨어", "SW", "반도체", 
    "네트워크", "5G", "6G", "메타버스", "사이버", "보안", "양자"
]

def fetch_nia_specialized_bills():
    url = "https://open.assembly.go.kr/portal/openapi/BILLRCP"
    params = {
        'Key': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 1000 
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        filtered_bills = []
        three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

        if 'BILLRCP' in data:
            rows = data['BILLRCP'][1].get('row', [])
            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                ppsl_dt = b.get('PPSL_DT', '')
                
                if ppsl_dt < three_months_ago:
                    continue
                
                clean_nm = bill_nm.upper().replace(" ", "")
                if any(k.upper() in clean_nm for k in MONITORING_KEYWORDS):
                    filtered_bills.append({
                        'date': ppsl_dt,
                        'title': bill_nm,
                        'proposer': b.get('PPSR_NM', '의원 등'),
                        'link': b.get('LINK_URL', '')
                    })
        return filtered_bills
    except Exception:
        return []

def send_nia_report(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🤖 [모니터링] 인공지능 및 디지털 관련 입법 리포트 ({len(bills)}건)"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    # 키워드 리스트를 문자열로 변환
    keyword_str = ", ".join(MONITORING_KEYWORDS)

    html = f"""
    <html><body style="font-family: 'Malgun Gothic', sans-serif; line-height: 1.6;">
        <h2 style="color: #1a73e8; border-left: 4px solid #1a73e8; padding-left: 10px;">인공지능 및 디지털 관련 입법 모니터링</h2>
        <p>최근 <b>3개월(90일)</b> 동안 접수된 의안 중 인공지능 및 디지털 관련 법안입니다.<br>
        총 <b>{len(bills)}건</b>의 의안이 자동 검색되었습니다.</p>
        
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px; font-size: 13px; color: #555;">
            <strong>🔍 검색 키워드:</strong> {keyword_str}
        </div>
    """
    
    if not bills:
        html += "<p style='color: #666;'>현재 해당 기간 내 조건과 일치하는 신규 법안이 없습니다.</p>"
    else:
        html += "<table border='1' style='border-collapse: collapse; width: 100%; border-color: #e0e0e0;'>"
        html += "<tr style='background:#f1f3f4;'><th>접수일</th><th>의안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:10px; text-align:center; font-size: 13px;'>{b['date']}</td><td style='padding:10px;'><a href='{b['link']}' style='font-weight:bold; color:#1a73e8; text-decoration: none;'>{b['title']}</a></td><td style='padding:10px; text-align:center; font-size: 13px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    
    html += f"""
        <p style="margin-top: 20px; font-size: 11px; color: #999;">본 메일은 국회 Open API를 통해 자동 생성되었습니다. (발송시각: {datetime.now().strftime('%Y-%m-%d %H:%M')})</p>
    </body></html>
    """
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    nia_bills = fetch_nia_specialized_bills()
    send_nia_report(nia_bills)
