import requests
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [환경 변수] GitHub Secrets 설정을 다시 확인해 주세요.
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def fetch_bills_final():
    # 명세서(image_2ac3ff.png) 기준 공식 엔드포인트
    url = "https://open.assembly.go.kr/portal/openapi/BILLRCPV2"
    
    # [수정] 명세서와 동일하게 대소문자 매칭 (Key, Type, pIndex, pSize)
    params = {
        'Key': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 10 
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # 테스트를 위해 모든 필터링을 제거하고 최근 10건을 그대로 담습니다.
        all_bills = []
        if 'BILLRCPV2' in data:
            rows = data['BILLRCPV2'][1].get('row', [])
            for b in rows:
                all_bills.append({
                    'date': b.get('PPSL_DT', ''),
                    'title': b.get('BILL_NM', ''),
                    'proposer': b.get('PPSR_NM', '의원 등'),
                    'link': b.get('LINK_URL', '')
                })
        return all_bills, data # 원본 데이터도 함께 반환
    except Exception as e:
        return [], {"error": str(e)}

def send_final_email(bills, raw_log):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🚀 [성공기원] 국회 데이터 최종 수신 테스트 ({len(bills)}건)"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body>
        <h2 style="color: #27ae60;">✅ 국회 API 최종 데이터 검증</h2>
        <p>필터링을 끄고 최신 접수 데이터 10건을 호출한 결과입니다.</p>
    """
    
    if not bills:
        html += f"<p style='color: red;'>여전히 데이터가 없습니다. 서버 응답: {raw_log}</p>"
    else:
        html += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        html += "<tr style='background:#f4f4f4;'><th>접수일</th><th>의안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:8px;'>{b['date']}</td><td style='padding:8px;'>{b['title']}</td><td style='padding:8px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    
    html += f"<br><p><b>[디버그 로그]:</b> {raw_log}</p></body></html>"
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    bills_list, raw_response = fetch_bills_final()
    send_final_email(bills_list, raw_response)
