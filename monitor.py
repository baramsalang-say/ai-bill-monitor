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
    # 명세서(image_3628c4.png) 기준 공식 주소
    url = "https://open.assembly.go.kr/portal/openapi/ALLBILL"
    
    # NIA 핵심 키워드 셋
    keywords = ["인공지능", "AI", "데이터", "지능정보", "디지털", "알고리즘", "클라우드", "소프트웨어", "정보통신"]
    filtered_bills = []
    
    # [핵심] 최근 상정된 법안 2,000건을 전수 조사합니다 (100건씩 20페이지)
    for page in range(1, 21):
        params = {
            'KEY': API_KEY,
            'Type': 'json',
            'pIndex': page,
            'pSize': 100
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if 'ALLBILL' in data:
                rows = data['ALLBILL'][1].get('row', [])
                if not rows: break # 더 이상 데이터가 없으면 중단
                
                for b in rows:
                    bill_nm = b.get('BILL_NM', '')
                    # 모든 키워드에 대해 띄어쓰기 무시하고 대조
                    clean_nm = bill_nm.upper().replace(" ", "")
                    if any(k.upper() in clean_nm for k in keywords):
                        filtered_bills.append({
                            'date': b.get('PPSL_DT', ''),
                            'title': bill_nm,
                            'proposer': b.get('PPSR_NM', ''),
                            'link': b.get('LINK_URL', '')
                        })
            else:
                # 에러 메시지가 온 경우 (예: 310, 300 등)
                print(f"Page {page} 에러 응답: {data.get('RESULT')}")
                break
                
        except Exception as e:
            print(f"Page {page} 통신 에러: {e}")
            break
            
    # 중복 제거 및 최신순 정렬
    unique_bills = {b['link']: b for b in filtered_bills}.values()
    return sorted(unique_bills, key=lambda x: x['date'], reverse=True)

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [NIA] 국회 입법 동향 리포트 - {len(bills)}건 발견"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body>
        <h2 style="color: #002d56;">📊 NIA 지능정보사회 입법 모니터링 (2,000건 전수조사)</h2>
        <p>국회 API 최신 데이터 2,000건을 분석한 실시간 결과입니다.</p>
    """
    if not bills:
        html += "<p style='color: red; font-weight: bold;'>최근 2,000건의 의안 중 관련 키워드 법안이 발견되지 않았습니다.</p>"
    else:
        html += f"<p>총 <b>{len(bills)}건</b>의 주요 법안이 감지되었습니다.</p>"
        html += "<table border='1' style='border-collapse: collapse; width: 100%; font-size: 13px;'>"
        html += "<tr style='background:#002d56; color: white;'><th>제안일</th><th>의안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:8px; text-align:center;'>{b['date']}</td><td style='padding:8px;'><a href='{b['link']}'>{b['title']}</a></td><td style='padding:8px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    html += "</body></html>"

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
    print(f"발송 완료 (발견: {len(bills)}건)")

if __name__ == "__main__":
    results = fetch_bills()
    send_email(results)
