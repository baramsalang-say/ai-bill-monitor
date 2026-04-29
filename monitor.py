import requests
from bs4 import BeautifulSoup
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [환경 변수] - 메일 발송용만 사용
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def fetch_bills_scraping():
    # 국회 의안정보시스템 검색 결과 페이지 (AI/데이터 관련 최신순)
    # 키워드 '인공지능'으로 직접 검색한 결과 페이지를 타겟팅합니다.
    url = "https://likms.assembly.go.kr/bill/main/main.do"
    search_url = "https://likms.assembly.go.kr/bill/billLList.do"
    
    params = {
        'searchStr': '인공지능', # 가장 확실한 키워드 하나로 시작
        'pIndex': 1,
        'pSize': 50
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(search_url, params=params, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        bills = []
        # 국회 웹사이트의 테이블 구조를 분석하여 데이터 추출
        table = soup.find('table', {'class': 'table'})
        if not table: return []

        rows = table.find_all('tr')[1:] # 헤더 제외
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 5:
                bill_nm = cols[1].find('a').text.strip()
                bill_id_raw = cols[1].find('a')['onclick']
                # onclick 이벤트에서 billId 추출
                bill_id = bill_id_raw.split("'")[1]
                
                bills.append({
                    'BILL_NM': bill_nm,
                    'PROPOSE_DT': cols[4].text.strip(),
                    'PROPOSER': cols[3].text.strip(),
                    'BILL_ID': bill_id
                })
        return bills
    except Exception as e:
        print(f"스크래핑 실패: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[긴급/최종] 국회 AI 입법 동향 리포트 - {len(bills)}건 발견"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html_content = f"""
    <html>
    <body>
        <h2 style="color: #c0392b;">🏛️ NIA 지능정보 입법 동향 (웹 다이렉트 수집)</h2>
        <p>API를 거치지 않고 국회 의안정보시스템에서 직접 수집한 실시간 데이터입니다.</p>
        <table border="1" style="border-collapse: collapse; width: 100%; font-family: sans-serif;">
            <tr style="background-color: #c0392b; color: white;">
                <th style="padding: 10px;">제안일</th>
                <th style="padding: 10px;">의안명</th>
                <th style="padding: 10px;">제안자</th>
                <th style="padding: 10px;">링크</th>
            </tr>
    """
    
    if not bills:
        html_content += "<tr><td colspan='4' style='padding: 30px; text-align: center;'>현재 웹사이트 상에서도 검색되는 신규 법안이 없습니다.</td></tr>"
    else:
        for b in bills:
            link = f"https://likms.assembly.go.kr/bill/billDetail.do?billId={b['BILL_ID']}"
            html_content += f"""
            <tr>
                <td style="padding: 10px;">{b['PROPOSE_DT']}</td>
                <td style="padding: 10px;"><b>{b['BILL_NM']}</b></td>
                <td style="padding: 10px;">{b['PROPOSER']}</td>
                <td style="padding: 10px;"><a href="{link}">원문 보기</a></td>
            </tr>"""
    
    html_content += "</table></body></html>"
    msg.attach(MIMEText(html_content, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    # 라이브러리 설치 확인용 (GitHub Actions 실행 시 필요)
    # pip install beautifulsoup4
    results = fetch_bills_scraping()
    send_email(results)
