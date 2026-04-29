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

# [키워드] NIA 정책 연구를 위해 검색 범위를 조금 더 넓게 설정 (유사 단어 포함)
KEYWORDS = ["인공지능", "AI", "알고리즘", "데이터", "딥러닝", "머신러닝", "지능정보", "자동화", "챗GPT", "지능", "로봇", "디지털", "클라우드"]

def fetch_bills():
    # pSize를 최대치(1000)로 설정하여 가장 많은 양의 최신 데이터를 확보
    url = f"https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu?KEY={API_KEY}&Type=json&pIndex=1&pSize=1000"
    
    try:
        response = requests.get(url, timeout=15)
        raw_json = response.json()
        
        status = "정상"
        rows = []
        
        if 'nwvrqwxyaytdsfvhu' in raw_json:
            rows = raw_json['nwvrqwxyaytdsfvhu'][1].get('row', [])
        
        # 1년 전 날짜
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        filtered = []
        for b in rows:
            bill_name = b.get('BILL_NM', '')
            propose_dt = b.get('PROPOSE_DT', '')
            
            # 날짜 및 키워드 필터링 (띄어쓰기 무시)
            if propose_dt and propose_dt >= one_year_ago:
                clean_name = bill_name.upper().replace(" ", "")
                if any(k.upper() in clean_name for k in KEYWORDS):
                    filtered.append(b)
        
        # 만약 결과가 너무 없다면 키워드 하나만이라도 걸리는 '테스트용 데이터' 추가 시도
        # (실제로 법안이 없을 경우 사용자에게 시스템 작동 여부를 알리기 위함)
        if not filtered and rows:
            status = "정상(AI관련법안없음)"

        filtered.sort(key=lambda x: x.get('PROPOSE_DT', ''), reverse=True)
        return filtered, status
        
    except Exception as e:
        return [], f"오류: {str(e)}"

def send_email(bills, status):
    msg = MIMEMultipart('alternative')
    # 제목에 건수 표시하여 직관적으로 확인 가능하게 함
    msg['Subject'] = f"[보고서] 국회 AI 관련 입법 동향 - {len(bills)}건 ({datetime.now().strftime('%Y-%m-%d')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html_content = f"""
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: 'Malgun Gothic', sans-serif; font-size: 13px; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background-color: #003366; color: white; }}
            tr:nth-child(even) {{ background-color: #f8f9fa; }}
            .link-btn {{ color: #003366; text-decoration: none; font-weight: bold; }}
            .badge {{ display: inline-block; padding: 3px 7px; background-color: #e74c3c; color: white; border-radius: 3px; font-size: 11px; }}
        </style>
    </head>
    <body>
        <h2 style="color: #003366;">🏛️ NIA 지능정보사회 입법동향 보고</h2>
        <div style="background-color: #f0f4f7; padding: 15px; border-left: 5px solid #003366; margin-bottom: 20px;">
            <b>조회 대상:</b> 최근 1,000개 의안 (제22대 국회 포함 전수조사)<br>
            <b>검색 결과:</b> 총 <b>{len(bills)}건</b>의 법안이 발견되었습니다.<br>
            <b>시스템 상태:</b> {status}
        </div>
        <table>
            <tr><th style="width: 15%;">제안일</th><th style="width: 55%;">의안명</th><th style="width: 15%;">제안자</th><th style="width: 15%;">상세보기</th></tr>
    """
    
    if not bills:
        html_content += f"<tr><td colspan='4' style='padding: 30px; text-align: center; color: #7f8c8d;'>최근 상정된 의안 중 설정한 키워드에 해당하는 법안이 없습니다.</td></tr>"
    else:
        for b in bills:
            bill_id = b.get('BILL_ID', '')
            link = f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
            html_content += f"<tr><td>{b.get('PROPOSE_DT','-')}</td><td><b>{b.get('BILL_NM','-')}</b></td><td>{b.get('PROPOSER','-')}</td><td><a href='{link}' class='link-btn'>원문보기</a></td></tr>"
    
    html_content += "</table><p style='color: grey; font-size: 11px;'>※ 본 보고서는 국회 오픈 API를 통해 매월 정기적으로 발송됩니다.</p></body></html>"
    msg.attach(MIMEText(html_content, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    found_bills, status_msg = fetch_bills()
    send_email(found_bills, status_msg)
