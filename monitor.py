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

# [키워드]
KEYWORDS = ["인공지능", "AI", "알고리즘", "데이터", "딥러닝", "머신러닝", "지능정보", "자동화"]

def fetch_bills():
    # 국회 API 포털의 표준 통합 의안 서비스 엔드포인트: ALLBILLS
    # URL 구조를 국회 API 포털 매뉴얼의 표준형으로 재구성했습니다.
    url = f"https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu?KEY={API_KEY}&Type=json&pIndex=1&pSize=1000"
    
    try:
        response = requests.get(url, timeout=15)
        raw_json = response.json()
        
        status = "연결 성공"
        rows = []
        
        # 국회 API는 서비스 명칭(nwvrqwxyaytdsfvhu)이 키값으로 들어옵니다.
        if 'nwvrqwxyaytdsfvhu' in raw_json:
            rows = raw_json['nwvrqwxyaytdsfvhu'][1].get('row', [])
            status = "정상 수집"
        elif 'RESULT' in raw_json:
            status = f"응답 메시지: {raw_json['RESULT'].get('MESSAGE')}"
            # 만약 서비스명을 못 찾으면 다른 이름(ALLBILLS 관련)으로 시도
            if 'ERROR-310' in str(raw_json):
                # 마지막 대안 주소 (일부 키에서 사용하는 구조)
                alt_url = f"https://open.assembly.go.kr/portal/openapi/nzmimehqvxbmqvpif?KEY={API_KEY}&Type=json&pIndex=1&pSize=1000"
                alt_res = requests.get(alt_url, timeout=10).json()
                if 'nzmimehqvxbmqvpif' in alt_res:
                    rows = alt_res['nzmimehqvxbmqvpif'][1].get('row', [])
                    status = "정상 수집(대안)"
        
        filtered = []
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        for b in rows:
            bill_name = b.get('BILL_NM', '')
            propose_dt = b.get('PROPOSE_DT', '')
            
            if propose_dt and propose_dt >= one_year_ago:
                if any(k.upper() in bill_name.upper().replace(" ", "") for k in KEYWORDS):
                    filtered.append(b)
        
        filtered.sort(key=lambda x: x.get('PROPOSE_DT', ''), reverse=True)
        return filtered, status
        
    except Exception as e:
        return [], f"시스템 장애: {str(e)}"

def send_email(bills, status):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[보고서] 제22대 국회 AI 법안 모니터링 - {len(bills)}건 ({datetime.now().strftime('%Y-%m-%d')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html_content = f"""
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: 'Malgun Gothic', sans-serif; font-size: 14px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #004080; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f7fb; }}
            .link-btn {{ color: #004080; text-decoration: none; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h2 style="color: #004080;">🏛️ NIA 지능정보사회 입법동향 (최종교정)</h2>
        <div style="background-color: #f0f4f8; padding: 15px; border-left: 5px solid #004080; margin-bottom: 20px;">
            <b>API 상태:</b> {status}<br>
            <b>결과:</b> 최근 1년 내 관련 의안 <b>{len(bills)}건</b> 발견
        </div>
        <table>
            <tr><th>제안일</th><th>의안명</th><th>제안자</th><th>상세보기</th></tr>
    """
    
    if not bills:
        html_content += f"<tr><td colspan='4' style='padding: 30px; text-align: center;'>조건에 맞는 법안이 없습니다. (상태: {status})</td></tr>"
    else:
        for b in bills:
            bill_id = b.get('BILL_ID', '')
            link = f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
            html_content += f"<tr><td>{b.get('PROPOSE_DT','-')}</td><td><b>{b.get('BILL_NM','-')}</b></td><td>{b.get('PROPOSER','-')}</td><td><a href='{link}' class='link-btn'>원문보기</a></td></tr>"
    
    html_content += "</table></body></html>"
    msg.attach(MIMEText(html_content, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    found_bills, status_msg = fetch_bills()
    send_email(found_bills, status_msg)
