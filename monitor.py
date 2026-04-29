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

# [키워드] 검색 누락을 방지하기 위해 키워드를 더 정교화함
KEYWORDS = ["인공지능", "AI", "알고리즘", "데이터", "딥러닝", "머신러닝", "지능정보", "자동화", "지능", "로봇", "디지털"]

def fetch_bills():
    # 가장 원천적인 '의안정보목록' API 주소로 변경
    # 이 주소는 국회에서 발의되는 모든 종류의 의안이 실시간으로 담기는 통로입니다.
    url = f"https://open.assembly.go.kr/portal/openapi/nzmimehqvxbmqvpif?KEY={API_KEY}&Type=json&pIndex=1&pSize=1000"
    
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        
        # 1년 전 날짜 설정
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # 데이터 추출 (API 서비스 명칭에 맞게 구조 파싱)
        rows = []
        if 'nzmimehqvxbmqvpif' in data:
            rows = data['nzmimehqvxbmqvpif'][1].get('row', [])
        
        print(f"DEBUG: 수집된 전체 로우 수 = {len(rows)}") # 로그 확인용

        filtered = []
        for b in rows:
            bill_name = b.get('BILL_NM', '')
            propose_dt = b.get('PROPOSE_DT', '')
            
            # 날짜 비교 및 키워드 매칭
            if propose_dt and propose_dt >= one_year_ago:
                clean_name = bill_name.upper().replace(" ", "")
                if any(k.upper() in clean_name for k in KEYWORDS):
                    filtered.append(b)
        
        filtered.sort(key=lambda x: x['PROPOSE_DT'], reverse=True)
        return filtered, "성공"
        
    except Exception as e:
        return [], f"오류 발생: {str(e)}"

def send_email(bills, status):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[보고서] NIA 국회 AI 관련 법안 모니터링 - {len(bills)}건 ({datetime.now().strftime('%m월 %d일')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html_content = f"""
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: 'Malgun Gothic', sans-serif; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #003366; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f6f9; }}
            .link-btn {{ color: #003366; text-decoration: none; font-weight: bold; border-bottom: 1px solid #003366; }}
        </style>
    </head>
    <body>
        <h2 style="color: #003366;">🏛️ NIA 지능정보사회 입법 동향 보고</h2>
        <div style="background-color: #e7eff6; padding: 15px; border-left: 5px solid #003366; margin-bottom: 20px;">
            <b>상태:</b> {status} (최근 1,000개 의안 전수조사)<br>
            <b>결과:</b> 1년 내 관련 법안 <b>{len(bills)}건</b> 발견
        </div>
        <table>
            <tr>
                <th>제안일</th>
                <th>의안명</th>
                <th>제안자</th>
                <th>상세정보</th>
            </tr>
    """
    
    if not bills:
        html_content += "<tr><td colspan='4' style='padding: 30px; text-align: center;'>최근 상정된 관련 의안이 데이터베이스에 아직 반영되지 않았습니다.</td></tr>"
    else:
        for b in bills:
            bill_id = b.get('BILL_ID', '')
            link = f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
            html_content += f"""
            <tr>
                <td>{b['PROPOSE_DT']}</td>
                <td><b>{b['BILL_NM']}</b></td>
                <td>{b['PROPOSER']}</td>
                <td><a href="{link}" class="link-btn">원문 보기</a></td>
            </tr>
            """
    
    html_content += "</table></body></html>"
    msg.attach(MIMEText(html_content, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    found_bills, status_msg = fetch_bills()
    send_email(found_bills, status_msg)
