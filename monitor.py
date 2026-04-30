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
    # [수정] 명세서 최상단에 명시된 공식 요청주소 사용
    url = "https://open.assembly.go.kr/portal/openapi/ALLBILL"
    
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 500  # 한 번에 500건 전수 조사
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # 키워드 (띄어쓰기 무관하게 매칭)
        keywords = ["인공지능", "AI", "데이터", "지능정보", "디지털", "알고리즘", "클라우드", "소프트웨어"]
        filtered_bills = []

        # 명세서 출력값 No.27까지의 필드명을 기준으로 파싱
        if 'ALLBILL' in data:
            rows = data['ALLBILL'][1].get('row', [])
            for b in rows:
                bill_nm = b.get('BILL_NM', '') # 출력값 No.5
                ppsl_dt = b.get('PPSL_DT', '') # 출력값 No.9 (제안일)
                ppsr_nm = b.get('PPSR_NM', '') # 출력값 No.7 (제안자명)
                link_url = b.get('LINK_URL', '') # 출력값 No.27 (링크URL)

                clean_nm = bill_nm.upper().replace(" ", "")
                if any(k.upper() in clean_nm for k in keywords):
                    filtered_bills.append({
                        'date': ppsl_dt,
                        'title': bill_nm,
                        'proposer': ppsr_nm,
                        'link': link_url
                    })
        
        # 제안일 기준 내림차순 정렬
        filtered_bills.sort(key=lambda x: x['date'], reverse=True)
        return filtered_bills
    except Exception as e:
        print(f"오류 발생: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [명세서 반영] NIA 국회 입법 동향 - {len(bills)}건 발견"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body>
        <h2 style="color: #002d56;">📊 NIA 지능정보사회 입법 모니터링 (명세서 v1 기준)</h2>
        <p>명세서에 명시된 <b>ALLBILL</b> 엔드포인트를 통해 수집된 결과입니다.</p>
    """
    if not bills:
        html += "<p style='color: red;'>최신 500건의 의안 중 관련 키워드가 포함된 법안이 없습니다.</p>"
    else:
        html += f"<p>총 <b>{len(bills)}건</b>의 법안이 발견되었습니다.</p>"
        html += "<table border='1' style='border-collapse: collapse; width: 100%; border-color: #ddd;'>"
        html += "<tr style='background:#002d56; color: white;'><th>제안일</th><th>의안명</th><th>제안자</th></tr>"
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
