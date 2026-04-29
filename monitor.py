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
    # 국회 의안정보시스템 검색 주소
    url = "https://likms.assembly.go.kr/bill/billLList.do"
    params = {
        'searchStr': '인공지능',
        'pIndex': 1,
        'pSize': 15
    }
    # 실제 브라우저처럼 보이게 하는 헤더 (차단 방지)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
    }

    try:
        print("데이터 수집 시작...")
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status() # 접속 실패 시 에러 발생
        
        soup = BeautifulSoup(response.text, 'html.parser')
        bills = []
        
        # 테이블 행 찾기 (가장 표준적인 경로)
        rows = soup.find_all('tr')
        print(f"총 {len(rows)}개의 행 발견")

        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 4:
                title_elem = cols[1].find('a')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    proposer = cols[3].get_text(strip=True)
                    date = cols[4].get_text(strip=True)
                    
                    # 상세 링크 추출
                    onclick = title_elem.get('onclick', '')
                    bill_id = ""
                    if "billId=" in onclick or "'" in onclick:
                        try:
                            bill_id = onclick.split("'")[1]
                        except: pass
                    
                    bills.append({
                        'title': title,
                        'proposer': proposer,
                        'date': date,
                        'link': f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}" if bill_id else "#"
                    })
        
        print(f"최종 {len(bills)}건 수집 완료")
        return bills
    except Exception as e:
        print(f"상세 에러 발생: {e}")
        return []

def send_email(bills):
    # 데이터가 없어도 시스템 생존 확인을 위해 메일은 보냅니다.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[최종확인] 국회 입법 모니터링 시스템 보고 ({datetime.now().strftime('%m/%d')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    if not bills:
        content = "<p>수집된 데이터가 없습니다. 국회 사이트 구조가 변경되었거나 접근이 차단되었을 수 있습니다.</p>"
    else:
        content = f"<h3>최신 인공지능 관련 법안 ({len(bills)}건)</h3>"
        content += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        content += "<tr style='background:#f2f2f2;'><th>날짜</th><th>법안명</th><th>제안자</th></tr>"
        for b in bills:
            content += f"<tr><td>{b['date']}</td><td><a href='{b['link']}'>{b['title']}</a></td><td>{b['proposer']}</td></tr>"
        content += "</table>"

    msg.attach(MIMEText(content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MY_EMAIL, EMAIL_PW)
            server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
        print("메일 발송 성공")
    except Exception as e:
        print(f"메일 발송 에러: {e}")

if __name__ == "__main__":
    data = fetch_bills()
    send_email(data)
