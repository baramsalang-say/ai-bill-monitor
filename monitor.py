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

# [키워드] 최대한 넓게 잡기
KEYWORDS = ["인공지능", "AI", "알고리즘", "데이터", "딥러닝", "머신러닝", "지능정보", "자동화"]

def fetch_bills():
    # 국회 오픈 API 포털의 가장 기본적이고 최신인 '의안정보' 서비스 주소 (ALLBILLS)
    # 22대 국회 데이터가 포함된 통합 서비스 주소입니다.
    url = f"https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu?KEY={API_KEY}&Type=json&pIndex=1&pSize=1000"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # 1. API 자체 에러 확인
        if 'head' in data and 'errorCode' in data['head']:
            error_code = data['head']['errorCode']
            if error_code != "INFO-000":
                print(f"API 서버 응답 에러: {error_code}")
                return [], f"API 에러 ({error_code})"

        # 1년 전 날짜 (비교용)
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # 2. 데이터 추출 시작
        if 'nwvrqwxyaytdsfvhu' in data:
            rows = data['nwvrqwxyaytdsfvhu'][1].get('row', [])
            print(f"총 {len(rows)}건의 원본 데이터를 가져왔습니다.") # 디버깅용
            
            filtered = []
            for b in rows:
                bill_name = b.get('BILL_NM', '')
                propose_dt = b.get('PROPOSE_DT', '')
                
                # 1년 이내 데이터만 필터
                if propose_dt >= one_year_ago:
                    clean_name = bill_name.upper().replace(" ", "")
                    if any(k.upper() in clean_name for k in KEYWORDS):
                        filtered.append(b)
            
            filtered.sort(key=lambda x: x['PROPOSE_DT'], reverse=True)
            return filtered, "정상"
        else:
            return [], "데이터 구조 없음"
            
    except Exception as e:
        print(f"수집 실패: {e}")
        return [], str(e)

def send_email(bills, status):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[점검] 국회 AI 법안 모니터링 - {len(bills)}건 발견 (상태: {status})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    # NIA 연구원용 리포트 디자인
    html_content = f"""
    <html>
    <body>
        <h2 style="color: #2c3e50;">🏛️ 제22대 국회 AI 법안 모니터링 (NIA 전용)</h2>
        <div style="background-color: #f8f9fa; padding: 15px; border-left: 5px solid #004792; margin-bottom: 20px;">
            <b>시스템 상태:</b> {status}<br>
            <b>원본 데이터 확인:</b> 국회 최신 의안 {('1000' if status=='정상' else '0')}건 수집 시도<br>
            <b>검색 결과:</b> 최근 1년 내 AI 관련 법안 총 {len(bills)}건 발견
        </div>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #004792; color: white;">
                <th style="padding: 10px;">제안일</th>
                <th style="padding: 10px;">의안명</th>
                <th style="padding: 10px;">제안자</th>
                <th style="padding: 10px;">상세</th>
            </tr>
    """
    
    if not bills:
        html_content += f"<tr><td colspan='4' style='padding: 30px; text-align: center;'>데이터가 없습니다. (상태: {status})</td></tr>"
    else:
        for b in bills:
            bill_id = b.get('BILL_ID', '')
            link = f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
            html_content += f"""
            <tr>
                <td style="padding: 10px;">{b['PROPOSE_DT']}</td>
                <td style="padding: 10px;"><b>{b['BILL_NM']}</b></td>
                <td style="padding: 10px;">{b['PROPOSER']}</td>
                <td style="padding: 10px;"><a href="{link}">원문</a></td>
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
