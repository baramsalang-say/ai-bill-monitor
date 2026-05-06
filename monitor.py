import requests
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [환경 변수] GitHub Secrets 설정
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def fetch_nia_specialized_bills():
    url = "https://open.assembly.go.kr/portal/openapi/BILLRCP"
    
    # 최근 3개월 데이터를 충분히 커버하기 위해 pSize를 1000건으로 확대합니다.
    # (국회 의안은 보통 3개월에 수백 건~천 건 내외가 접수됩니다.)
    params = {
        'Key': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 1000 
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # [NIA 전문 키워드] 디지털, IT, ICT 및 미래 기술 포괄
        keywords = [
            "인공지능", "AI", "데이터", "디지털", "지능정보", "ICT", "정보통신", 
            "플랫폼", "알고리즘", "클라우드", "소프트웨어", "SW", "반도체", 
            "네트워크", "5G", "6G", "메타버스", "사이버", "보안", "양자"
        ]
        
        filtered_bills = []
        three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

        if 'BILLRCP' in data:
            rows = data['BILLRCP'][1].get('row', [])
            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                ppsl_dt = b.get('PPSL_DT', '') # 접수일
                
                # 1. 날짜 필터: 최근 3개월(90일) 이내 데이터만
                if ppsl_dt < three_months_ago:
                    continue
                
                # 2. 키워드 필터: 지능정보사회 관련 단어 매칭
                clean_nm = bill_nm.upper().replace(" ", "")
                if any(k.upper() in clean_nm for k in keywords):
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
    msg['Subject'] = f"🏛️ [NIA] 지능정보사회 입법 동향 리포트 (최근 3개월: {len(bills)}건)"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body style="font-family: 'Malgun Gothic', sans-serif;">
        <h2 style="color: #002d56;">📊 NIA 지능정보사회 입법 모니터링</h2>
        <p>최근 <b>3개월(90일)</b> 동안 접수된 의안 중 지능정보사회 관련 주요 법안입니다.</p>
    """
    
    if not bills:
        html += "<p style='color: #666;'>현재 해당 기간 내 조건과 일치하는 신규 법안이 없습니다.</p>"
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
    nia_bills = fetch_nia_specialized_bills()
    send_nia_report(nia_bills)
