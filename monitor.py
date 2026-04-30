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

def fetch_bills():
    # 명세서에 명시된 의안 접수목록 공식 주소
    url = "https://open.assembly.go.kr/portal/openapi/BILLRCPV2"
    
    # ERROR-300 방지를 위해 명세서의 기본값(1, 100)을 엄격히 준수하여 요청
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 100 
    }

    try:
        # 명세서 가이드대로 인증키와 기본 인자를 실어서 호출
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # NIA 핵심 모니터링 키워드
        keywords = ["인공지능", "AI", "데이터", "지능정보", "디지털", "알고리즘", "클라우드", "소프트웨어"]
        filtered_bills = []

        # 서버 응답 구조(BILLRCPV2 -> row)에 맞춰 파싱
        if 'BILLRCPV2' in data:
            rows = data['BILLRCPV2'][1].get('row', [])
            for b in rows:
                bill_nm = b.get('BILL_NM', '')     # 의안명
                ppsl_dt = b.get('PPSL_DT', '')     # 접수일
                ppsr_nm = b.get('PPSR_NM', '의원 등') # 제안자
                link_url = b.get('LINK_URL', '')   # 상세 링크

                clean_nm = bill_nm.upper().replace(" ", "")
                if any(k.upper() in clean_nm for k in keywords):
                    filtered_bills.append({
                        'date': ppsl_dt,
                        'title': bill_nm,
                        'proposer': ppsr_nm,
                        'link': link_url
                    })
        return filtered_bills
    except Exception as e:
        print(f"데이터 처리 오류: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [최종교정] NIA 국회 입법 모니터링 - {len(bills)}건 발견"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body>
        <h2 style="color: #002d56;">📊 NIA 지능정보사회 의안 접수 리포트</h2>
        <p>파라미터 규격을 재조정하여 <b>정상 수집</b>된 실시간 데이터입니다.</p>
    """
    if not bills:
        html += "<p style='color: #e74c3c;'>현재 접수된 의안 중 키워드와 일치하는 법안이 없습니다.</p>"
    else:
        html += f"<p>총 <b>{len(bills)}건</b>의 법안이 감지되었습니다.</p>"
        html += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        html += "<tr style='background:#f8f9fa;'><th>접수일</th><th>의안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:8px; text-align:center;'>{b['date']}</td><td style='padding:8px;'><a href='{b['link']}'>{b['title']}</a></td><td style='padding:8px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    html += "</body></html>"

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    results = fetch_bills()
    send_email(results)
