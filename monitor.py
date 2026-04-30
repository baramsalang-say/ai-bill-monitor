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
    # 명세서(image_3628c4.png) 기준 의안정보 통합 API 주소
    url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
    
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 50 # 우선 확인을 위해 50건만 호출
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        
        # [중요] 국회 서버가 주는 생얼 데이터를 로그에 무조건 찍습니다.
        print("===== 국회 API 응답 데이터 (Raw) 시작 =====")
        print(response.text[:1000]) # 앞부분 1000자 출력
        print("===== 국회 API 응답 데이터 (Raw) 끝 =====")
        
        data = response.json()
        
        # 날짜 및 키워드 기준
        date_limit = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
        keywords = ["인공지능", "AI", "데이터", "지능정보", "디지털", "알고리즘"]
        
        filtered_bills = []

        if 'nwvrqwxyaytdsfvhu' in data:
            rows = data['nwvrqwxyaytdsfvhu'][1].get('row', [])
            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                # 날짜 형식 보정 (하이픈 제거)
                raw_dt = b.get('PPSL_DT', '')
                ppsl_dt = raw_dt.replace("-", "").replace(".", "") if raw_dt else ""
                
                if ppsl_dt and ppsl_dt >= date_limit:
                    if any(k.upper() in bill_nm.upper().replace(" ", "") for k in keywords):
                        filtered_bills.append({
                            'date': raw_dt,
                            'title': bill_nm,
                            'proposer': b.get('PPSR_NM', ''),
                            'link': f"https://likms.assembly.go.kr/bill/billDetail.do?billId={b.get('BILL_ID')}"
                        })
        return filtered_bills
    except Exception as e:
        print(f"데이터 수집 중 에러 발생: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [최종테스트] 국회 입법 동향 리포트 - {len(bills)}건 ({datetime.now().strftime('%m/%d')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body>
        <h2>📊 NIA 지능정보사회 입법 동향 리포트</h2>
        <p>상태: 데이터 수집 로직 최종 점검 중</p>
    """
    if not bills:
        html += "<p style='color: red;'>조건에 맞는 법안이 없습니다. 로그를 확인해 주세요.</p>"
    else:
        html += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        html += "<tr style='background:#f2f2f2;'><th>날짜</th><th>법안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td>{b['date']}</td><td><a href='{b['link']}'>{b['title']}</a></td><td>{b['proposer']}</td></tr>"
        html += "</table>"
    html += "</body></html>"

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
    print("이메일 발송 완료!")

if __name__ == "__main__":
    results = fetch_bills()
    send_email(results)
