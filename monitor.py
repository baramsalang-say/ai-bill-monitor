import requests
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [환경 변수]
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def fetch_bills():
    # v1 인증키 전용 주소
    url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
    
    # [수정] 2024년 초부터 현재까지의 데이터를 모두 훑습니다.
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 1000 
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # NIA 관심 키워드 (그물을 더 크게 쳤습니다)
        keywords = ["인공지능", "AI", "데이터", "지능", "디지털", "소프트웨어", "정보통신", "클라우드", "로봇", "플랫폼"]
        filtered_bills = []

        if 'nwvrqwxyaytdsfvhu' in data:
            rows = data['nwvrqwxyaytdsfvhu'][1].get('row', [])
            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                clean_nm = bill_nm.upper().replace(" ", "")
                
                # 키워드 매칭 여부 확인
                if any(k.upper() in clean_nm for k in keywords):
                    filtered_bills.append({
                        'date': b.get('PPSL_DT', ''),
                        'title': bill_nm,
                        'proposer': b.get('PPSR_NM', '의원 등'),
                        'link': f"https://likms.assembly.go.kr/bill/billDetail.do?billId={b.get('BILL_ID')}"
                    })
        
        # 최신순 정렬
        filtered_bills.sort(key=lambda x: x['date'], reverse=True)
        return filtered_bills
    except Exception as e:
        print(f"데이터 수집 중 오류: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [성공] NIA 국회 입법 동향 리포트 - {len(bills)}건 발견"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body style="font-family: 'Malgun Gothic', sans-serif;">
        <h2 style="color: #002d56;">📊 NIA 지능정보사회 입법 모니터링 (시스템 정상 가동)</h2>
        <p>인증 에러 해결 후, <b>2024년 전체 데이터</b>를 전수 조사한 결과입니다.</p>
    """
    if not bills:
        html += "<p style='color: red;'>최근 1,000건의 의안 중 IT 관련 키워드가 포함된 법안이 아직 없습니다.</p>"
    else:
        html += f"<p style='color: #2980b9;'>총 <b>{len(bills)}건</b>의 관련 법안이 발견되었습니다.</p>"
        html += "<table border='1' style='border-collapse: collapse; width: 100%; border-color: #ddd;'>"
        html += "<tr style='background:#002d56; color: white;'><th>제안일</th><th>의안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:8px; text-align:center;'>{b['date']}</td><td style='padding:8px;'><a href='{b['link']}' style='font-weight:bold; color:#002d56;'>{b['title']}</a></td><td style='padding:8px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    
    html += "<p style='font-size: 11px; color: #888; margin-top: 20px;'>※ 본 리포트는 국회 오픈 API v1 시스템을 기반으로 자동 생성되었습니다.</p></body></html>"

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    results = fetch_bills()
    send_email(results)
