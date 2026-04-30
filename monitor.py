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
    # 의안목록전체 API (nzmimehqvxbmqvpif)
    url = "https://open.assembly.go.kr/portal/openapi/nzmimehqvxbmqvpif"
    
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 300 # 더 넓게 훑기 위해 300건으로 확대
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # 수집 기간을 최근 90일로 확장 (분기별 동향 파악 가능)
        date_limit = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
        
        # NIA 연구 도메인에 맞춘 확장 키워드 셋
        keywords = [
            "인공지능", "AI", "데이터", "지능정보", "디지털", "알고리즘", 
            "클라우드", "소프트웨어", "정보통신", "ICT", "플랫폼", "지능형",
            "로봇", "메타버스", "가상융합", "개인정보", "공공데이터"
        ]
        
        filtered_bills = []
        service_name = 'nzmimehqvxbmqvpif'

        if service_name in data:
            rows = data[service_name][1].get('row', [])
            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                raw_dt = b.get('PROPOSE_DT', '')
                ppsl_dt = raw_dt.replace("-", "") if raw_dt else ""
                
                if ppsl_dt and ppsl_dt >= date_limit:
                    # 모든 키워드에 대해 띄어쓰기 무시하고 대조
                    clean_nm = bill_nm.upper().replace(" ", "")
                    if any(k.upper() in clean_nm for k in keywords):
                        filtered_bills.append({
                            'date': raw_dt,
                            'title': bill_nm,
                            'proposer': b.get('PROPOSER', ''),
                            'link': f"https://likms.assembly.go.kr/bill/billDetail.do?billId={b.get('BILL_ID')}"
                        })
        return filtered_bills
    except Exception as e:
        print(f"데이터 수집 에러: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [NIA] 국회 입법 동향 보고 - {len(bills)}건 감지 ({datetime.now().strftime('%m/%d')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body style="font-family: 'Malgun Gothic', sans-serif; line-height: 1.6;">
        <h2 style="color: #003366; border-bottom: 2px solid #003366; padding-bottom: 10px;">📊 NIA 지능정보사회 입법 동향 (확장 키워드)</h2>
        <p>최근 90일간 상정된 의안 중 NIA 주요 관심 키워드 법안을 추출한 결과입니다.</p>
    """
    if not bills:
        html += "<p style='color: #e74c3c; font-weight: bold;'>현재 검색 조건(최근 90일, 확장 키워드)에 부합하는 신규 법안이 없습니다.</p>"
    else:
        html += f"<p style='color: #2980b9;'>총 <b>{len(bills)}건</b>의 법안이 발견되었습니다.</p>"
        html += "<table border='1' style='border-collapse: collapse; width: 100%; border-color: #ddd;'>"
        html += "<tr style='background:#f4f4f4;'><th>제안일</th><th>법안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:8px; text-align:center;'>{b['date']}</td><td style='padding:8px;'><a href='{b['link']}' style='color:#003366; text-decoration:none; font-weight:bold;'>{b['title']}</a></td><td style='padding:8px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    
    html += "<p style='font-size: 11px; color: #777; margin-top: 20px;'>※ 본 메일은 NIA 연구 업무 지원을 위해 국회 API를 기반으로 자동 생성되었습니다.</p></body></html>"

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
    print(f"이메일 발송 완료! (건수: {len(bills)})")

if __name__ == "__main__":
    results = fetch_bills()
    send_email(results)
