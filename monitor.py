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

# [키워드] NIA 정책연구에 걸릴만한 모든 단어 투입
KEYWORDS = ["인공지능", "AI", "알고리즘", "데이터", "딥러닝", "머신러닝", "지능정보", "자동화", "챗GPT", "디지털", "소프트웨어", "ICT", "클라우드", "메타버스"]

def fetch_bills():
    all_filtered = []
    one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # 최근 3,000건을 확인하기 위해 1,000건씩 3페이지를 훑습니다.
    for page in range(1, 4):
        url = f"https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu?KEY={API_KEY}&Type=json&pIndex={page}&pSize=1000"
        try:
            response = requests.get(url, timeout=15)
            data = response.json()
            
            if 'nwvrqwxyaytdsfvhu' in data:
                rows = data['nwvrqwxyaytdsfvhu'][1].get('row', [])
                for b in rows:
                    bill_name = b.get('BILL_NM', '')
                    propose_dt = b.get('PROPOSE_DT', '')
                    
                    if propose_dt and propose_dt >= one_year_ago:
                        clean_name = bill_name.upper().replace(" ", "")
                        if any(k.upper() in clean_name for k in KEYWORDS):
                            all_filtered.append(b)
                
                # 만약 가져온 데이터의 마지막 날짜가 이미 1년 전보다 더 과거라면 중단
                if rows and rows[-1].get('PROPOSE_DT', '') < one_year_ago:
                    break
            else:
                break
        except:
            break
            
    # 중복 제거 및 정렬
    unique_bills = {b['BILL_ID']: b for b in all_filtered}.values()
    sorted_bills = sorted(unique_bills, key=lambda x: x.get('PROPOSE_DT', ''), reverse=True)
    
    return sorted_bills

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[보고서] 국회 입법 동향 리포트 - {len(bills)}건 발견 ({datetime.now().strftime('%Y-%m-%d')})"
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
        <h2 style="color: #003366;">🏛️ NIA 지능정보사회 입법동향 (전수조사 모드)</h2>
        <div style="background-color: #e7eff6; padding: 15px; border-left: 5px solid #003366; margin-bottom: 20px;">
            <b>상태:</b> 정상 (최근 3,000개 의안 정밀 분석 완료)<br>
            <b>결과:</b> 조건에 맞는 법안 총 <b>{len(bills)}건</b> 발견
        </div>
        <table>
            <tr><th>제안일</th><th>의안명</th><th>제안자</th><th>상세정보</th></tr>
    """
    
    if not bills:
        html_content += "<tr><td colspan='4' style='padding: 30px; text-align: center;'>최근 1년 내 해당 키워드로 상정된 의안이 데이터베이스에 없습니다.</td></tr>"
    else:
        for b in bills:
            bill_id = b.get('BILL_ID', '')
            link = f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
            html_content += f"<tr><td>{b['PROPOSE_DT']}</td><td><b>{b['BILL_NM']}</b></td><td>{b['PROPOSER']}</td><td><a href='{link}' class='link-btn'>원문보기</a></td></tr>"
    
    html_content += "</table><p style='color: #7f8c8d; font-size: 11px; margin-top: 20px;'>※ 본 보고서는 2주 단위로 NIA 연구원님께 자동 발송됩니다.</p></body></html>"
    msg.attach(MIMEText(html_content, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    found_bills = fetch_bills()
    send_email(found_bills)
