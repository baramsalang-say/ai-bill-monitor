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

# [키워드] 검색 누락을 방지하기 위해 핵심 단어 위주로 최적화
KEYWORDS = ["인공지능", "AI", "데이터", "지능정보", "알고리즘", "디지털", "컴퓨팅", "소프트웨어", "챗GPT", "지능형"]

def fetch_bills():
    all_filtered = []
    # 22대 국회 개원일(2024년 5월 30일) 근처부터 조회하도록 충분히 설정
    limit_date = (datetime.now() - timedelta(days=500)).strftime('%Y-%m-%d')
    
    # 1,000건씩 5페이지(총 5,000건)를 샅샅이 뒤집니다.
    for page in range(1, 6):
        url = f"https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu?KEY={API_KEY}&Type=json&pIndex={page}&pSize=1000"
        try:
            response = requests.get(url, timeout=20)
            data = response.json()
            
            if 'nwvrqwxyaytdsfvhu' in data:
                rows = data['nwvrqwxyaytdsfvhu'][1].get('row', [])
                if not rows: break
                
                for b in rows:
                    bill_nm = b.get('BILL_NM', '')
                    propose_dt = b.get('PROPOSE_DT', '')
                    
                    if propose_dt and propose_dt >= limit_date:
                        # 띄어쓰기 무시하고 키워드 매칭
                        target_text = bill_nm.upper().replace(" ", "")
                        if any(k.upper() in target_text for k in KEYWORDS):
                            all_filtered.append(b)
                
                # 날짜가 너무 과거로 가면 중단
                if rows[-1].get('PROPOSE_DT', '') < limit_date:
                    break
            else:
                break
        except:
            break
            
    # 중복 제거 및 최신순 정렬
    unique_bills = {b['BILL_ID']: b for b in all_filtered}.values()
    return sorted(unique_bills, key=lambda x: x.get('PROPOSE_DT', ''), reverse=True)

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[입법동향] NIA 국회 AI/데이터 법안 모니터링 - {len(bills)}건 ({datetime.now().strftime('%m/%d')})"
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
            .link-btn {{ color: #003366; text-decoration: none; font-weight: bold; border-bottom: 1px solid #003366; }}
            .header-box {{ background-color: #f0f4f7; padding: 20px; border-left: 10px solid #003366; margin-bottom: 25px; }}
        </style>
    </head>
    <body>
        <div class="header-box">
            <h2 style="margin:0; color: #003366;">🏛️ NIA 지능정보 입법 동향 리포트</h2>
            <p style="margin: 10px 0 0 0;">검색 대상: 제22대 국회 상정 의안 5,000건 전수조사<br>
            발견된 법안: 총 <b>{len(bills)}건</b></p>
        </div>
        <table>
            <tr><th style="width:15%">제안일</th><th style="width:55%">법안명</th><th style="width:15%">제안자</th><th style="width:15%">상세보기</th></tr>
    """
    
    if not bills:
        html_content += "<tr><td colspan='4' style='padding:40px; text-align:center;'>현재 국회 데이터베이스에 관련 키워드의 최신 법안이 없습니다.</td></tr>"
    else:
        for b in bills:
            link = f"https://likms.assembly.go.kr/bill/billDetail.do?billId={b['BILL_ID']}"
            html_content += f"""
            <tr>
                <td>{b['PROPOSE_DT']}</td>
                <td><b>{b['BILL_NM']}</b></td>
                <td>{b['PROPOSER']}</td>
                <td><a href="{link}" class="link-btn">원문 보기</a></td>
            </tr>"""
    
    html_content += "</table><p style='color:grey; font-size:11px; margin-top:20px;'>※ 본 메일은 NIA 연구 업무를 위해 2주 단위로 자동 발송됩니다.</p></body></html>"
    msg.attach(MIMEText(html_content, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    results = fetch_bills()
    send_email(results)
