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

def fetch_bills():
    # 국회 통합 의안 API
    url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
    
    # [핵심] 파이썬에서 거르지 않고, API 서버 검색 엔진을 직접 이용합니다.
    # BILL_NM 파라미터에 검색어를 직접 넣습니다.
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 100,
        'BILL_NM': '인공지능'  # 서버에서 '인공지능' 포함된 것만 찾아오라고 시킴
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # 최근 1년치로 범위 대폭 확대 (22대 국회 전체 커버)
        date_limit = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        filtered_bills = []

        if 'nwvrqwxyaytdsfvhu' in data:
            rows = data['nwvrqwxyaytdsfvhu'][1].get('row', [])
            
            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                raw_dt = b.get('PPSL_DT', '')
                ppsl_dt = raw_dt.replace("-", "") if raw_dt else ""
                
                # 서버에서 이미 걸러왔지만, 날짜만 한 번 더 체크
                if ppsl_dt and ppsl_dt >= date_limit:
                    filtered_bills.append({
                        'date': raw_dt,
                        'title': bill_nm,
                        'proposer': b.get('PPSR_NM', ''),
                        'link': f"https://likms.assembly.go.kr/bill/billDetail.do?billId={b.get('BILL_ID')}"
                    })
        
        return filtered_bills
    except Exception as e:
        print(f"오류: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [최종] NIA 국회 AI 입법 동향 리포트 - {len(bills)}건 발견"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html>
    <body>
        <h2 style="color: #004792;">📊 NIA 지능정보사회 입법 동향 (서버 검색 모드)</h2>
        <p>국회 API 서버에서 '인공지능' 키워드로 직접 검색한 결과입니다.</p>
    """

    if not bills:
        html += "<p style='color: red;'>서버 검색 결과, 최근 1년 내 '인공지능' 키워드가 포함된 법안 데이터가 없습니다.</p>"
    else:
        html += f"<p>총 <b>{len(bills)}건</b>의 법안이 발견되었습니다.</p>"
        html += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        html += "<tr style='background:#f2f2f2;'><th>제안일</th><th>법안명</th><th>제안자</th><th>링크</th></tr>"
        for b in bills:
            html += f"<tr><td>{b['date']}</td><td>{b['title']}</td><td>{b['proposer']}</td><td><a href='{b['link']}'>원문</a></td></tr>"
        html += "</table>"
    
    html += "</body></html>"
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    results = fetch_bills()
    send_email(results)
