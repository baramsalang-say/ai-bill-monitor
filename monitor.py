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
    # [수정] 의안목록전체 API (nzmimehqvxbmqvpif) 주소로 변경
    # 이전 주소는 의원 인적사항이 섞여있어 이 주소가 가장 확실합니다.
    url = "https://open.assembly.go.kr/portal/openapi/nzmimehqvxbmqvpif"
    
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 200 # 넉넉하게 200건 조회
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # 날짜 및 키워드 기준
        date_limit = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
        keywords = ["인공지능", "AI", "데이터", "지능정보", "디지털", "알고리즘"]
        
        filtered_bills = []

        # API 응답 구조에 맞게 데이터 추출 (nzmimehqvxbmqvpif 기준)
        service_name = 'nzmimehqvxbmqvpif'
        if service_name in data:
            rows = data[service_name][1].get('row', [])
            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                # 제안일 (PROPOSE_DT)
                raw_dt = b.get('PROPOSE_DT', '')
                ppsl_dt = raw_dt.replace("-", "") if raw_dt else ""
                
                if ppsl_dt and ppsl_dt >= date_limit:
                    if any(k.upper() in bill_nm.upper().replace(" ", "") for k in keywords):
                        filtered_bills.append({
                            'date': raw_dt,
                            'title': bill_nm,
                            'proposer': b.get('PROPOSER', ''), # 제안자 필드
                            'link': f"https://likms.assembly.go.kr/bill/billDetail.do?billId={b.get('BILL_ID')}"
                        })
        return filtered_bills
    except Exception as e:
        print(f"데이터 수집 중 에러 발생: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [NIA] 국회 입법 동향 리포트 - {len(bills)}건 발견 ({datetime.now().strftime('%m/%d')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body style="font-family: 'Malgun Gothic', sans-serif;">
        <h2 style="color: #003366;">📊 NIA 지능정보사회 입법 동향 보고</h2>
        <p>최근 60일간 상정된 의안 중 핵심 키워드 법안을 추출한 결과입니다.</p>
    """
    if not bills:
        html += "<p style='color: #e74c3c;'>조회 기간 내 조건에 맞는 새로운 법안이 발견되지 않았습니다.</p>"
    else:
        html += "<table border='1' style='border-collapse: collapse; width: 100%; border: 1px solid #ddd;'>"
        html += "<tr style='background:#003366; color: white;'><th>제안일</th><th>법안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:8px;'>{b['date']}</td><td style='padding:8px;'><a href='{b['link']}'>{b['title']}</a></td><td style='padding:8px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    html += "</body></html>"

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
    print(f"이메일 발송 완료! (발견 건수: {len(bills)})")

if __name__ == "__main__":
    results = fetch_bills()
    send_email(results)
