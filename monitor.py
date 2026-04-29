import requests
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [보안 설정] GitHub Secrets에서 가져오기
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")

# [메일 설정] 요청하신 주소 반영
MY_EMAIL = "baramsalang@gmail.com"  # 발송용
RECEIVE_EMAIL = "jyjeong@nia.or.kr" # 수신용

# [키워드] 
KEYWORDS = ["인공지능", "AI", "알고리즘", "데이터", "딥러닝", "머신러닝", "지능정보", "자동화"]

def fetch_bills():
    # 국회 API 포털 전용 서비스 명칭: ntkfkaqyfhwswpicy (최신 의안정보)
    # 이 주소는 국회 API 포털에서 직접 키를 받은 경우 가장 안정적으로 작동합니다.
    url = f"https://open.assembly.go.kr/portal/openapi/ntkfkaqyfhwswpicy?KEY={API_KEY}&Type=json&pIndex=1&pSize=1000"
    
    try:
        response = requests.get(url, timeout=15)
        raw_json = response.json()
        
        # 1년 전 날짜
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        rows = []
        status = "연결 실패"
        
        # 국회 API 포털 응답 구조 파싱
        if 'ntkfkaqyfhwswpicy' in raw_json:
            rows = raw_json['ntkfkaqyfhwswpicy'][1].get('row', [])
            status = "정상 수집"
        elif 'RESULT' in raw_json:
            status = f"오류: {raw_json['RESULT'].get('MESSAGE')}"
            print(f"API 에러 상세: {raw_json['RESULT']}")
            
        filtered = []
        for b in rows:
            bill_name = b.get('BILL_NM', '')
            propose_dt = b.get('PROPOSE_DT', '')
            
            # 1. 날짜 필터 (최근 1년)
            if propose_dt and propose_dt >= one_year_ago:
                # 2. 키워드 필터 (공백 제거 매칭)
                if any(k.upper() in bill_name.upper().replace(" ", "") for k in KEYWORDS):
                    filtered.append(b)
        
        # 최신순 정렬
        filtered.sort(key=lambda x: x.get('PROPOSE_DT', ''), reverse=True)
        return filtered, status
        
    except Exception as e:
        return [], f"시스템 장애: {str(e)}"

def send_email(bills, status):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[보고서] NIA 국회 AI 입법 동향 - {len(bills)}건 발견 ({datetime.now().strftime('%Y-%m-%d')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html_content = f"""
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: 'Malgun Gothic', sans-serif; font-size: 14px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #002266; color: white; }}
            tr:nth-child(even) {{ background-color: #f4f7fa; }}
            .link-btn {{ color: #002266; text-decoration: none; font-weight: bold; border-bottom: 1px solid #002266; }}
            .summary {{ background-color: #f0f4f8; padding: 15px; border-left: 5px solid #002266; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <h2 style="color: #002266;">🏛️ 제22대 국회 AI 관련 법안 모니터링 (NIA)</h2>
        <div class="summary">
            <b>API 상태:</b> {status}<br>
            <b>조회 대상:</b> 최근 1,000개 의안 중 1년 내 데이터<br>
            <b>검색 결과:</b> 총 {len(bills)}건이 발견되었습니다.
        </div>
        <table>
            <tr>
                <th style="width: 15%;">제안일</th>
                <th style="width: 55%;">의안명</th>
                <th style="width: 15%;">제안자</th>
                <th style="width: 15%;">상세보기</th>
            </tr>
    """
    
    if not bills:
        html_content += f"<tr><td colspan='4' style='padding: 30px; text-align: center;'>조건에 맞는 법안이 없습니다. (상태: {status})</td></tr>"
    else:
        for b in bills:
            bill_id = b.get('BILL_ID', '')
            link = f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
            html_content += f"""
            <tr>
                <td>{b.get('PROPOSE_DT','-')}</td>
                <td><b>{b.get('BILL_NM','-')}</b></td>
                <td>{b.get('PROPOSER','-')}</td>
                <td><a href="{link}" class="link-btn">원문 보기</a></td>
            </tr>
            """
    
    html_content += "</table><p style='color: grey; font-size: 11px;'>본 메일은 국회 오픈 API 데이터를 바탕으로 자동 생성되었습니다.</p></body></html>"
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MY_EMAIL, EMAIL_PW)
            server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
        print(f"완료: {len(bills)}건 발송")
    except Exception as e:
        print(f"메일 발송 실패: {e}")

if __name__ == "__main__":
    found_bills, status_msg = fetch_bills()
    send_email(found_bills, status_msg)
