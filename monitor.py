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
    # 명세서 기준 엔드포인트
    url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
    
    # 1. 일단 가장 최신 데이터 1,000건을 무조건 가져옵니다 (필터링 없이)
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 1000  # 한 번에 1,000개를 긁어옵니다
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # 60일 전 날짜 계산
        date_limit = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        keywords = ["인공지능", "AI", "데이터", "지능정보", "디지털", "알고리즘", "지능", "로봇"]
        
        filtered_bills = []

        if 'nwvrqwxyaytdsfvhu' in data:
            rows = data['nwvrqwxyaytdsfvhu'][1].get('row', [])
            print(f"총 {len(rows)}건의 원본 데이터를 분석 중...")

            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                ppsl_dt = b.get('PPSL_DT', '') # 명세서 9번 제안일
                ppsr_nm = b.get('PPSR_NM', '') # 명세서 7번 제안자명
                bill_id = b.get('BILL_ID', '') # 명세서 2번 의안ID

                # 2. 파이썬이 직접 날짜와 키워드를 필터링합니다.
                if ppsl_dt and ppsl_dt >= date_limit:
                    clean_nm = bill_nm.upper().replace(" ", "")
                    if any(k.upper() in clean_nm for k in keywords):
                        filtered_bills.append({
                            'date': ppsl_dt,
                            'title': bill_nm,
                            'proposer': ppsr_nm,
                            'link': f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
                        })
        
        # 최신순 정렬
        filtered_bills.sort(key=lambda x: x['date'], reverse=True)
        return filtered_bills
    except Exception as e:
        print(f"오류 발생: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [NIA] 국회 입법 모니터링 리포트 - {len(bills)}건 발견 ({datetime.now().strftime('%m/%d')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: 'Malgun Gothic', sans-serif; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #004792; color: white; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .link-btn {{ color: #004792; font-weight: bold; text-decoration: none; }}
        </style>
    </head>
    <body>
        <h2>📊 NIA 지능정보사회 입법 동향 리포트</h2>
        <p>최근 60일간 상정된 의안 1,000건을 전수조사한 결과입니다.</p>
    """

    if not bills:
        html += "<p style='color: #e74c3c; font-weight: bold;'>최근 상정된 데이터 중 키워드에 부합하는 법안이 발견되지 않았습니다.</p>"
    else:
        html += "<table><tr><th>제안일</th><th>법안명</th><th>제안자</th><th>상세보기</th></tr>"
        for b in bills:
            html += f"""
            <tr>
                <td>{b['date']}</td>
                <td><b>{b['title']}</b></td>
                <td>{b['proposer']}</td>
                <td><a href='{b['link']}' class='link-btn'>원문 보기</a></td>
            </tr>
            """
        html += "</table>"
    
    html += "<p style='font-size: 12px; color: #777; margin-top: 20px;'>※ 본 메일은 국회 오픈 API 실시간 데이터를 바탕으로 자동 생성되었습니다.</p></body></html>"

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    results = fetch_bills()
    send_email(results)
