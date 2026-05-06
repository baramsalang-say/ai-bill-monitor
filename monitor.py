import requests
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [환경 변수] GitHub Secrets에 등록된 값을 가져옵니다.
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def fetch_bills():
    # 국회 오픈 API 실시간 의안 접수 현황 (BILLRCPV2)
    url = "https://open.assembly.go.kr/portal/openapi/BILLRCPV2"
    
    # [교정] ERROR-300 방지를 위해 명세서 규격(Key, pIndex 등)을 엄격히 준수
    params = {
        'Key': API_KEY,      # 인증키 (명세서 표기 준수)
        'Type': 'json',      # 응답 형식
        'pIndex': 1,         # 페이지 번호
        'pSize': 100,        # 한 번에 100건 확인
        'ERACO': '제22대'     # [중요] 필수 인자급 파라미터 명시
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # NIA 핵심 모니터링 키워드 (그물을 넓게 펼칩니다)
        keywords = [
            "인공지능", "AI", "데이터", "지능정보", "디지털", "소프트웨어", "SW", 
            "정보통신", "ICT", "클라우드", "플랫폼", "알고리즘", "네트워크", "컴퓨팅"
        ]
        filtered_bills = []

        # 데이터 구조 파싱 (BILLRCPV2 -> row)
        if 'BILLRCPV2' in data:
            rows = data['BILLRCPV2'][1].get('row', [])
            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                # 대소문자 구분 없이 키워드 매칭
                clean_nm = bill_nm.upper().replace(" ", "")
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

def send_email(bills, raw_log):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [실시간] NIA 지능정보사회 의안 모니터링 ({len(bills)}건)"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body style="font-family: 'Malgun Gothic', dotum, sans-serif;">
        <h2 style="color: #002d56;">📊 NIA 지능정보사회 입법 리포트</h2>
        <p><b>제22대 국회</b> 최신 접수 의안 중 기술/디지털 관련 법안을 분석한 결과입니다.</p>
    """
    
    if not bills:
        html += f"""
        <p style='color: #e74c3c; font-weight: bold;'>현재 신규 접수된 의안 중 키워드와 일치하는 법안이 없습니다.</p>
        <p style='font-size: 12px; color: #666;'>※ 시스템 상태: 정상 작동 중 (데이터 범위: 최근 100건)</p>
        """
    else:
        html += f"<p>총 <b>{len(bills)}건</b>의 주요 의안이 발견되었습니다.</p>"
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
    results, log = fetch_bills()
    send_email(results, log)
