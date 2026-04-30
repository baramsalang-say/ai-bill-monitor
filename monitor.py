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
    # 명세서에 나온 '의안정보 통합 API' 엔드포인트
    url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
    
    # 넉넉하게 최근 60일치 조회
    start_date = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
    
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 500
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        keywords = ["인공지능", "AI", "데이터", "지능정보", "디지털", "알고리즘"]
        filtered_bills = []

        if 'nwvrqwxyaytdsfvhu' in data:
            rows = data['nwvrqwxyaytdsfvhu'][1].get('row', [])
            for b in rows:
                # 명세서의 출력명(BILL_NM, PPSL_DT, PPSR_NM) 적용
                bill_nm = b.get('BILL_NM', '')
                ppsl_dt = b.get('PPSL_DT', '')  # 제안일
                ppsr_nm = b.get('PPSR_NM', '')  # 제안자명
                bill_id = b.get('BILL_ID', '')

                # 날짜 필터링 및 키워드 매칭
                if ppsl_dt >= start_date:
                    if any(k in bill_nm.replace(" ", "").upper() for k in keywords):
                        filtered_bills.append({
                            'date': ppsl_dt,
                            'title': bill_nm,
                            'proposer': ppsr_nm,
                            'link': f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
                        })
        return filtered_bills
    except Exception as e:
        print(f"데이터 수집 중 오류: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [NIA] 국회 입법 동향 리포트 - {len(bills)}건 발견 ({datetime.now().strftime('%m/%d')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    if not bills:
        html = "<h3>최근 60일간 상정된 관련 키워드 법안이 없습니다.</h3>"
    else:
        html = f"<h3>최근 60일간 상정된 AI/데이터 법안 (총 {len(bills)}건)</h3>"
        html += "<table border='1' style='border-collapse: collapse; width: 100%; font-family: sans-serif;'>"
        html += "<tr style='background:#f2f2f2;'><th>제안일</th><th>법안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td>{b['date']}</td><td><b><a href='{b['link']}'>{b['title']}</a></b></td><td>{b['proposer']}</td></tr>"
        html += "</table>"

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    results = fetch_bills()
    send_email(results)
