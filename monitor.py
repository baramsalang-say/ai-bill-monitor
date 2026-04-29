import requests
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [보안 설정]
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

# [필터링 키워드] - 더 넓은 범위를 잡기 위해 키워드 보강
KEYWORDS = ["인공지능", "AI", "알고리즘", "데이터", "딥러닝", "머신러닝", "지능정보", "챗GPT", "자동화"]

def fetch_bills():
    # 최근 1년치를 안전하게 가져오기 위해 1000건 설정
    # 날짜 필터를 제거하고 목록을 먼저 가져온 뒤 날짜와 키워드를 파이썬에서 거릅니다.
    url = f"https://open.assembly.go.kr/portal/openapi/nzmimehqvxbmqvpif?KEY={API_KEY}&Type=json&pIndex=1&pSize=1000"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # 1년 전 날짜 (비교용)
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        if 'nzmimehqvxbmqvpif' in data:
            rows = data['nzmimehqvxbmqvpif'][1].get('row', [])
            
            filtered = []
            for b in rows:
                bill_name = b.get('BILL_NM', '')
                propose_dt = b.get('PROPOSE_DT', '')
                
                # 1. 날짜 필터 (1년 이내)
                if propose_dt >= one_year_ago:
                    # 2. 키워드 필터
                    if any(k.upper() in bill_name.upper().replace(" ", "") for k in KEYWORDS):
                        filtered.append(b)
            
            # 최신순 정렬
            filtered.sort(key=lambda x: x['PROPOSE_DT'], reverse=True)
            return filtered
        return []
    except Exception as e:
        print(f"데이터 수집 중 오류 발생: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    # 제목에 검색된 건수 표시
    msg['Subject'] = f"[보고서] 국회 AI 관련 법안 모니터링 - {len(bills)}건 검색됨 ({datetime.now().strftime('%Y-%m-%d')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html_content = f"""
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: 'Malgun Gothic', sans-serif; font-size: 14px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #4A90E2; color: white; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .link-btn {{ color: #4A90E2; text-decoration: none; font-weight: bold; }}
            .summary {{ margin-bottom: 20px; padding: 15px; background-color: #eef6ff; border-left: 5px solid #4A90E2; }}
        </style>
    </head>
    <body>
        <h2 style="color: #2c3e50;">📊 국회 AI 관련 법안 모니터링 결과</h2>
        <div class="summary">
            <b>조회 기간:</b> 최근 1년<br>
            <b>검색 키워드:</b> {', '.join(KEYWORDS)}<br>
            <b>검색 결과:</b> 총 {len(bills)}건
        </div>
        <table>
            <tr>
                <th style="width: 15%;">제안일</th>
                <th style="width: 55%;">법안명</th>
                <th style="width: 15%;">제안자</th>
                <th style="width: 15%;">상세보기</th>
            </tr>
    """
    
    if not bills:
        html_content += "<tr><td colspan='4' style='text-align: center; padding: 30px;'>검색 조건에 맞는 최신 법안이 없습니다.</td></tr>"
    else:
        for b in bills:
            # 상세보기 링크가 없을 경우 검색 페이지로 대체
            bill_id = b.get('BILL_ID', '')
            link = f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}" if bill_id else "#"
            
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
        <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">※ 본 보고서는 공공데이터포털 API 데이터를 바탕으로 자동 생성되었습니다.</p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MY_EMAIL, EMAIL_PW)
            server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
        print(f"성공: {len(bills)}건 발송")
    except Exception as e:
        print(f"실패: {e}")

if __name__ == "__main__":
    found_bills = fetch_bills()
    send_email(found_bills)
