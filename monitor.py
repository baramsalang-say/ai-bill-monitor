import requests
from bs4 import BeautifulSoup
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [환경 변수]
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def fetch_bills():
    # 국회 의안정보시스템 검색 (인공지능 키워드)
    url = "https://likms.assembly.go.kr/bill/billLList.do"
    params = {
        'searchStr': '인공지능',
        'pIndex': 1,
        'pSize': 20 # 최신 20건만 우선 확인
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'lxml')
        
        bills = []
        # 테이블의 데이터 행들을 찾습니다.
        table = soup.select_list('table.table tbody tr') or soup.find_all('tr')
        
        for row in table:
            cols = row.find_all('td')
            if len(cols) > 5:
                title_elem = cols[1].find('a')
                if title_elem:
                    title = title_elem.text.strip()
                    proposer = cols[3].text.strip()
                    date = cols[4].text.strip()
                    # 링크 생성을 위한 ID 추출
                    bill_id = title_elem.get('onclick', '').split("'")[1] if "'" in title_elem.get('onclick', '') else ""
                    
                    bills.append({
                        'title': title,
                        'proposer': proposer,
                        'date': date,
                        'link': f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}" if bill_id else "#"
                    })
        return bills
    except Exception as e:
        print(f"수집 실패: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[최종교정] NIA 국회 입법 동향 리포트 - {len(bills)}건 발견"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html>
    <body style="font-family: sans-serif;">
        <h2 style="color: #2980b9;">🏛️ 국회 의안정보 실시간 모니터링 (NIA)</h2>
        <p>국회 홈페이지에서 직접 수집한 최신 AI 관련 법안입니다.</p>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th style="padding: 10px;">제안일</th><th style="padding: 10px;">법안명</th><th style="padding: 10px;">제안자</th>
            </tr>
    """
    for b in bills:
        html += f"<tr><td style='padding:8px;'>{b['date']}</td><td style='padding:8px;'><b><a href='{b['link']}'>{b['title']}</a></b></td><td style='padding:8px;'>{b['proposer']}</td></tr>"
    
    html += "</table></body></html>"
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    data = fetch_bills()
    send_email(data)
