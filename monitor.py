import requests
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [환경 변수] GitHub Secrets 설정을 다시 확인해 주세요.
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def fetch_bills_expanded():
    # 명세서 기준 실시간 의안 접수 현황 엔드포인트
    url = "https://open.assembly.go.kr/portal/openapi/BILLRCPV2"
    
    # [교정] ERACO를 포함하여 최신 100건을 훑습니다.
    params = {
        'Key': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 100,
        'ERACO': '제22대' 
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # [키워드 확장] NIA 관심 도메인을 모두 포함하는 광범위 그물망
        keywords = [
            "인공지능", "AI", "데이터", "지능정보", "디지털", "소프트웨어", "SW", 
            "정보통신", "ICT", "클라우드", "플랫폼", "알고리즘", "네트워크", "컴퓨팅"
        ]
        filtered_bills = []

        if 'BILLRCPV2' in data:
            rows = data['BILLRCPV2'][1].get('row', [])
            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                clean_nm = bill_nm.upper().replace(" ", "")
                # 확장된 키워드 중 하나라도 포함되면 수집
                if any(k.upper() in clean_nm for k in keywords):
                    filtered_bills.append({
                        'date': b.get('PPSL_DT', ''),
                        'title': bill_nm,
                        'proposer': b.get('PPSR_NM', '의원 등'),
                        'link': b.get('LINK_URL', '')
                    })
        return filtered_bills, data
    except Exception as e:
        return [], {"error": str(e)}

def send_expanded_email(bills, raw_log):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [NIA] 국회 입법 동향 리포트 (수집 결과: {len(bills)}건)"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body style="font-family: sans-serif;">
        <h2 style="color: #002d56;">📊 NIA 지능정보사회 입법 모니터링</h2>
        <p><b>제22대 국회</b>의 최신 접수 의안 100건을 정밀 분석한 결과입니다.</p>
    """
    
    if not bills:
        # 데이터가 없을 경우, 시스템은 정상임을 알리는 로그 노출
        html += f"""
        <p style='color: #e74c3c; font-weight: bold;'>현재 NIA 관심 키워드(AI, 데이터 등)에 부합하는 신규 접수 의안이 없습니다.</p>
        <p style='font-size: 12px; color: #666;'>※ 시스템 상태: 정상 (API 응답 코드: {raw_log.get('BILLRCPV2', [{{'head': [{{'RESULT': {{'CODE': 'Unknown'}}]}}]}})[0]['head'][0]['RESULT']['CODE']})</p>
        """
    else:
        html += f"<p>총 <b>{len(bills)}건</b>의 주요 법안이 감지되었습니다.</p>"
        html += "<table border='1' style='border-collapse: collapse; width: 100%; border-color: #ddd;'>"
        html += "<tr style='background:#f8f9fa;'><th>접수일</th><th>의안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:8px; text-align:center;'>{b['date']}</td><td style='padding:8px;'><a href='{b['link']}' style='font-weight:bold; color:#002d56;'>{b['title']}</a></td><td style='padding:8px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    
    html += "</body></html>"
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    results, log = fetch_bills_expanded()
    send_expanded_email(results, log)
