import requests
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [필독] GitHub Secrets의 ASSEMBLY_API_KEY를 '683ce973958443b6bae5d2065bbcf243'로 꼭 업데이트하세요.
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def fetch_bills():
    # 제22대 국회 의안 접수 현황 API 주소
    url = "https://open.assembly.go.kr/portal/openapi/BILLRCPV2"
    
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 500  # 접수된 최신 의안 500건을 전수조사
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # NIA 연구 도메인 키워드 (실제 법안명에 쓰이는 용어 중심)
        keywords = ["인공지능", "AI", "데이터", "지능정보", "디지털", "소프트웨어", "정보통신", "클라우드", "플랫폼", "알고리즘"]
        filtered_bills = []

        if 'BILLRCPV2' in data:
            rows = data['BILLRCPV2'][1].get('row', [])
            for b in rows:
                bill_nm = b.get('BILL_NM', '')     # 의안명
                ppsl_dt = b.get('PPSL_DT', '')     # 접수일 (YYYY-MM-DD)
                ppsr_nm = b.get('PPSR_NM', '의원 등') # 제안자/발의자
                link_url = b.get('LINK_URL', '')   # 의안 상세 페이지 링크

                # 키워드 매칭 (공백 제거 후 대조)
                clean_nm = bill_nm.upper().replace(" ", "")
                if any(k.upper() in clean_nm for k in keywords):
                    filtered_bills.append({
                        'date': ppsl_dt,
                        'title': bill_nm,
                        'proposer': ppsr_nm,
                        'link': link_url
                    })
        
        # 접수일 기준 최신순 정렬
        filtered_bills.sort(key=lambda x: x['date'], reverse=True)
        return filtered_bills
    except Exception as e:
        print(f"API 데이터 수집 오류: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [NIA] 국회 신규 의안 접수 모니터링 - {len(bills)}건 발견"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body style="font-family: 'Malgun Gothic', sans-serif; line-height: 1.6;">
        <h2 style="color: #002d56; border-bottom: 2px solid #002d56; padding-bottom: 10px;">📊 실시간 국회 의안 접수 리포트 (NIA)</h2>
        <p>제22대 국회에 새롭게 접수된 의안 중 지능정보사회 관련 법안을 추출한 결과입니다.</p>
    """
    if not bills:
        html += "<p style='color: #e74c3c; font-weight: bold;'>최근 접수된 의안 중 모니터링 키워드에 부합하는 법안이 없습니다.</p>"
    else:
        html += f"<p style='color: #2980b9;'>총 <b>{len(bills)}건</b>의 법안이 감지되었습니다.</p>"
        html += "<table border='1' style='border-collapse: collapse; width: 100%; border: 1px solid #ddd;'>"
        html += "<tr style='background:#f8f9fa;'><th>접수일</th><th>의안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:10px; text-align:center;'>{b['date']}</td><td style='padding:10px;'><a href='{b['link']}' style='font-weight:bold; color:#002d56; text-decoration:none;'>{b['title']}</a></td><td style='padding:10px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    
    html += "<p style='font-size: 11px; color: #888; margin-top: 20px;'>※ 국회 오픈 API(BILLRCPV2)를 통해 NIA 연구 업무 지원을 위해 자동 생성되었습니다.</p></body></html>"

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
    print(f"발송 완료 (건수: {len(bills)})")

if __name__ == "__main__":
    results = fetch_bills()
    send_email(results)
