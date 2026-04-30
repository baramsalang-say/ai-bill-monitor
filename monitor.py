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
    url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
    
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 1000 
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # 비교를 위해 하이픈 없는 날짜 형식 준비 (예: 20260301)
        date_limit = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
        keywords = ["인공지능", "AI", "데이터", "지능정보", "디지털", "알고리즘", "지능", "로봇"]
        
        filtered_bills = []

        if 'nwvrqwxyaytdsfvhu' in data:
            rows = data['nwvrqwxyaytdsfvhu'][1].get('row', [])
            
            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                # 날짜 데이터에서 하이픈 제거 (2026-04-30 -> 20260430)
                raw_dt = b.get('PPSL_DT', '')
                ppsl_dt = raw_dt.replace("-", "") if raw_dt else ""
                
                ppsr_nm = b.get('PPSR_NM', '')
                bill_id = b.get('BILL_ID', '')

                # 날짜 비교 (숫자형 문자열 비교)
                if ppsl_dt and ppsl_dt >= date_limit:
                    clean_nm = bill_nm.upper().replace(" ", "")
                    if any(k.upper() in clean_nm for k in keywords):
                        filtered_bills.append({
                            'date': raw_dt, # 표시용은 원본 사용
                            'title': bill_nm,
                            'proposer': ppsr_nm,
                            'link': f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
                        })
        
        filtered_bills.sort(key=lambda x: x['date'], reverse=True)
        return filtered_bills
    except Exception as e:
        print(f"오류: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    # 제목에 시도 횟수나 상태를 알 수 있게 표시
    msg['Subject'] = f"🏛️ [최종교정] 국회 입법 모니터링 - {len(bills)}건 발견 ({datetime.now().strftime('%m/%d')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html>
    <body>
        <h2>📊 NIA 지능정보사회 입법 동향 (날짜형식 보정판)</h2>
        <p>최근 60일 내 상정된 의안 {len(bills)}건이 검색되었습니다.</p>
    """

    if not bills:
        html += "<p style='color: red;'>데이터를 1,000건 훑었으나 조건에 맞는 법안이 없습니다. (날짜 비교 로직 점검 완료)</p>"
    else:
        html += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        html += "<tr style='background:#f2f2f2;'><th>제안일</th><th>법안명</th><th>제안자</th><th>상세보기</th></tr>"
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
