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
    # [수정] v1 인증키와 호환되는 의안정보 API 주소
    url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
    
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 300 
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # 22대 국회 개원 이후(2024.05.30) 데이터 타겟
        date_limit = "20240530" 
        keywords = ["인공지능", "AI", "데이터", "지능정보", "디지털", "알고리즘", "지능형", "플랫폼"]
        
        filtered_bills = []

        # v1 엔드포인트 명칭에 맞춰 파싱
        if 'nwvrqwxyaytdsfvhu' in data:
            rows = data['nwvrqwxyaytdsfvhu'][1].get('row', [])
            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                # v1 명세서 기준 제안일 필드는 PPSL_DT입니다
                raw_dt = b.get('PPSL_DT', '')
                ppsl_dt = raw_dt.replace("-", "") if raw_dt else ""
                
                if ppsl_dt and ppsl_dt >= date_limit:
                    clean_nm = bill_nm.upper().replace(" ", "")
                    if any(k.upper() in clean_nm for k in keywords):
                        filtered_bills.append({
                            'date': raw_dt,
                            'title': bill_nm,
                            'proposer': b.get('PPSR_NM', '의원 등'),
                            'link': f"https://likms.assembly.go.kr/bill/billDetail.do?billId={b.get('BILL_ID')}"
                        })
        return filtered_bills
    except Exception as e:
        print(f"데이터 수집 중 에러: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [NIA] 국회 입법 동향 보고 - {len(bills)}건 발견"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body style="font-family: 'Malgun Gothic', sans-serif;">
        <h2 style="color: #002d56; border-left: 5px solid #002d56; padding-left: 10px;">📊 국회 지능정보사회 입법 동향 (v1 인증 최적화)</h2>
        <p>인증 에러(310) 해결 후 <b>정상 수집된 의안 데이터</b> 리스트입니다.</p>
    """
    if not bills:
        html += "<p style='color: #c0392b; font-weight: bold;'>조회된 데이터 중 키워드와 일치하는 법안이 없습니다.</p>"
    else:
        html += f"<p>총 <b>{len(bills)}건</b>의 주요 법안이 감지되었습니다.</p>"
        html += "<table border='1' style='border-collapse: collapse; width: 100%; border: 1px solid #ddd; font-size: 13px;'>"
        html += "<tr style='background:#002d56; color: white;'><th>제안일</th><th>의안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:10px; text-align:center;'>{b['date']}</td><td style='padding:10px;'><a href='{b['link']}' style='font-weight:bold; color:#002d56;'>{b['title']}</a></td><td style='padding:10px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    
    html += "<p style='font-size: 11px; color: #888; margin-top: 20px;'>※ 본 리포트는 국회 API v1 시스템을 통해 자동 생성되었습니다.</p></body></html>"

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
    print(f"이메일 발송 완료! (건수: {len(bills)})")

if __name__ == "__main__":
    results = fetch_bills()
    send_email(results)
