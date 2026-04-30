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
    
    # [핵심 수정] 명세서의 '기본인자' 변수명을 대소문자별로 이중 세팅하여 누락 방지
    params = {
        'KEY': API_KEY,      # 대문자 버전
        'Key': API_KEY,      # 명세서 표기 버전
        'Type': 'json',
        'pIndex': 1,
        'pSize': 10
    }

    try:
        # 요청 시 인자 누락이 없도록 명확히 전달
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        all_bills = []
        # 응답 구조 확인 및 데이터 추출
        if 'BILLRCPV2' in data:
            rows = data['BILLRCPV2'][1].get('row', [])
            for b in rows:
                all_bills.append({
                    'date': b.get('PPSL_DT', ''),
                    'title': b.get('BILL_NM', ''),
                    'proposer': b.get('PPSR_NM', '의원 등'),
                    'link': b.get('LINK_URL', '')
                })
        return all_bills, data
    except Exception as e:
        return [], {"error": str(e)}

def send_final_email(bills, raw_log):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🚀 [최종 교정] 국회 데이터 수신 성공 여부 확인 ({len(bills)}건)"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body>
        <h2 style="color: #27ae60;">✅ 국회 API 파라미터 교정 테스트</h2>
        <p>명세서의 대소문자 규격(Key, pIndex 등)을 엄격히 적용한 결과입니다.</p>
    """
    
    if not bills:
        html += f"<p style='color: red; font-weight: bold;'>여전히 데이터가 없습니다. 서버 응답 전문을 확인하세요.</p>"
    else:
        html += f"<p>총 <b>{len(bills)}건</b>의 데이터를 성공적으로 가져왔습니다!</p>"
        html += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        html += "<tr style='background:#f4f4f4;'><th>접수일</th><th>의안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:8px;'>{b['date']}</td><td style='padding:8px;'>{b['title']}</td><td style='padding:8px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    
    html += f"<br><hr><p style='color:#666;'><b>[서버 응답 원문]:</b> {raw_log}</p></body></html>"
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    bills_list, raw_response = fetch_bills_final()
    send_final_email(bills_list, raw_response)
