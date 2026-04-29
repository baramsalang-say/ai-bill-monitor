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

# [키워드] 아주 단순한 키워드로 테스트 (하나라도 걸리게 함)
KEYWORDS = ["인공지능", "AI", "데이터", "지능", "디지털", "정보"]

def fetch_bills():
    # pSize를 100으로 줄여서 최신 데이터 위주로 확실히 응답받기
    url = f"https://open.assembly.go.kr/portal/openapi/nzmimehqvxbmqvpif?KEY={API_KEY}&Type=json&pIndex=1&pSize=100"
    
    try:
        response = requests.get(url, timeout=15)
        raw_json = response.json()
        
        # 진단용: API 응답의 첫 부분을 텍스트로 저장
        debug_info = str(raw_json)[:500] 
        
        rows = []
        if 'nzmimehqvxbmqvpif' in raw_json:
            rows = raw_json['nzmimehqvxbmqvpif'][1].get('row', [])
        
        filtered = []
        for b in rows:
            # 모든 필드값을 합쳐서 키워드가 있는지 검사 (필드명 변경 대비)
            full_text = " ".join([str(val) for val in b.values()]).upper()
            if any(k.upper() in full_text for k in KEYWORDS):
                filtered.append(b)
        
        return filtered, f"수집성공(총 {len(rows)}건 중 {len(filtered)}건 필터됨)", debug_info
        
    except Exception as e:
        return [], f"오류: {str(e)}", ""

def send_email(bills, status, debug_info):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[진단보고서] 국회 API 수집 테스트 ({status})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html_content = f"""
    <html>
    <body>
        <h2 style="color: #d35400;">🔍 시스템 정밀 진단 모드</h2>
        <div style="background-color: #fdf2e9; padding: 15px; border-left: 5px solid #d35400; margin-bottom: 20px;">
            <b>현재 상태:</b> {status}<br>
            <b>API 원본 샘플:</b> <code style="font-size: 11px;">{debug_info}</code>
        </div>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #e67e22; color: white;">
                <th>제안일</th><th>의안명</th><th>제안자</th>
            </tr>
    """
    
    if not bills:
        html_content += "<tr><td colspan='3' style='padding: 20px; text-align: center;'>키워드에 매칭되는 데이터가 없습니다. 원본 샘플을 확인해주세요.</td></tr>"
    else:
        for b in bills:
            html_content += f"<tr><td>{b.get('PROPOSE_DT','-')}</td><td>{b.get('BILL_NM','-')}</td><td>{b.get('PROPOSER','-')}</td></tr>"
    
    html_content += "</table></body></html>"
    msg.attach(MIMEText(html_content, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    found_bills, status_msg, debug_text = fetch_bills()
    send_email(found_bills, status_msg, debug_text)
