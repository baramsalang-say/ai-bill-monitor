import requests
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [보안 설정] GitHub Secrets에서 값을 가져옵니다.
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")

# [메일 설정] 
MY_EMAIL = "baramsalang@gmail.com"  # 발송용 지메일 계정
RECEIVE_EMAIL = "jyjeong@nia.or.kr" # 결과 보고서를 받을 계정

# [필터링 설정] 감시할 키워드
KEYWORDS = ["인공지능", "AI", "알고리즘", "데이터", "딥러닝", "머신러닝", "지능정보"]

def fetch_bills():
    # [기간 설정] 테스트를 위해 최근 1년(365일) 데이터를 조회합니다.
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    
    url = f"https://open.assembly.go.kr/portal/openapi/nzmimehqvxbmqvpif?KEY={API_KEY}&Type=json&pIndex=1&pSize=500&PROPOSE_DT={start_date}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if 'nzmimehqvxbmqvpif' in data:
            rows = data['nzmimehqvxbmqvpif'][1].get('row', [])
            # 제목에 키워드가 포함된 법안만 필터링 (공백 제거 후 대소문자 구분 없이 비교)
            filtered = [b for b in rows if any(k.upper() in b['BILL_NM'].upper().replace(" ", "") for k in KEYWORDS)]
            # 최신순 정렬
            filtered.sort(key=lambda x: x['PROPOSE_DT'], reverse=True)
            return filtered
        return []
    except Exception as e:
        print(f"데이터 수집 중 오류 발생: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[보고서] 최근 1년 AI 관련 국회 법안 모니터링 ({datetime.now().strftime('%Y-%m-%d')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    # HTML 표 형식 본문 구성
    html_content = f"""
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: sans-serif; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f8f9fa; color: #333; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .link-btn {{ color: #007bff; text-decoration: none; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h2 style="color: #2c3e50;">📊 국회 AI 관련 법안 모니터링 결과</h2>
        <p>최근 1년간 상정된 의안 중 키워드(<b>{', '.join(KEYWORDS)}</b>)가 포함된 결과입니다.</p>
        <table>
            <tr>
                <th>제안일</th>
                <th>법안명</th>
                <th>제안자</th>
                <th>상세보기</th>
            </tr>
    """
    
    if not bills:
        html_content += "<tr><td colspan='4' style='text-align: center;'>검색된 법안이 없습니다.</td></tr>"
    else:
        for b in bills:
            link = b.get('DETAIL_LINK', '#')
            html_content += f"""
            <tr>
                <td>{b['PROPOSE_DT']}</td>
                <td><b>{b['BILL_NM']}</b></td>
                <td>{b['PROPOSER']}</td>
                <td><a href="{link}" class="link-btn">원문 보기</a></td>
            </tr>
            """
    
    html_content += """
        </table>
        <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">※ 본 메일은 설정된 주기에 따라 자동으로 발송되는 시스템 보고서입니다.</p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MY_EMAIL, EMAIL_PW)
            server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
        print(f"[{RECEIVE_EMAIL}] 주소로 총 {len(bills)}건 발송 완료!")
    except Exception as e:
        print(f"메일 발송 중 오류 발생: {e}")

if __name__ == "__main__":
    found_bills = fetch_bills()
    send_email(found_bills)
