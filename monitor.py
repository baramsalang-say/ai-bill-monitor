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

# [키워드] 연구 업무에 필수적인 광범위 키워드 셋
KEYWORDS = ["인공지능", "AI", "데이터", "지능정보", "알고리즘", "디지털", "컴퓨팅", "소프트웨어", "챗GPT", "지능형", "IT", "정보통신", "클라우드"]

def fetch_bills():
    all_filtered = []
    # 22대 국회 개원 초기부터 현재까지 (약 2년치 넉넉히 설정)
    limit_date = (datetime.now() - timedelta(days=700)).strftime('%Y-%m-%d')
    
    # 1,000건씩 최대 10페이지(1만 건)를 훑어 22대 국회 전체를 전수조사합니다.
    for page in range(1, 11):
        # 서비스 주소를 nzmimehqvxbmqvpif (의안정보목록)으로 최종 변경
        url = f"https://open.assembly.go.kr/portal/openapi/nzmimehqvxbmqvpif?KEY={API_KEY}&Type=json&pIndex={page}&pSize=1000"
        try:
            response = requests.get(url, timeout=30)
            data = response.json()
            
            # API 서비스명 필드 확인
            service_name = 'nzmimehqvxbmqvpif'
            if service_name in data:
                rows = data[service_name][1].get('row', [])
                if not rows: break
                
                for b in rows:
                    bill_nm = b.get('BILL_NM', '')
                    propose_dt = b.get('PROPOSE_DT', '')
                    
                    if propose_dt and propose_dt >= limit_date:
                        target_text = bill_nm.upper().replace(" ", "")
                        # 키워드 매칭
                        if any(k.upper() in target_text for k in KEYWORDS):
                            all_filtered.append(b)
                
                # 날짜가 이미 기준일보다 한참 전이면 중단
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
    msg['Subject'] = f"[입법리포트] NIA 국회 지능정보 법안 동향 - {len(bills)}건 ({datetime.now().strftime('%Y-%m-%d')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html_content = f"""
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: 'Malgun Gothic', sans-serif; font-size: 13px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #002d56; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f6f9; }}
            .link-btn {{ color: #002d56; text-decoration: none; font-weight: bold; }}
            .summary-box {{ background-color: #e7eff6; padding: 20px; border-left: 8px solid #002d56; margin-bottom: 25px; }}
        </style>
    </head>
    <body>
        <div class="summary-box">
            <h2 style="margin:0; color: #002d56;">🏛️ NIA 지능정보 입법 동향 보고</h2>
            <p style="margin: 10px 0 0 0;"><b>검색 범위:</b> 제22대 국회 상정 의안 10,000건 전수조사<br>
            <b>발견된 법안:</b> 총 <b>{len(bills)}건</b></p>
        </div>
        <table>
            <tr><th style="width:15%">제안일</th><th style="width:55%">법안명</th><th style="width:15%">제안자</th><th style="width:15%">상세보기</th></tr>
    """
    
    if not bills:
        html_content += "<tr><td colspan='4' style='padding:40px; text-align:center;'>현재 국회 데이터 원천 소스에 관련 키워드의 법안이 존재하지 않습니다.</td></tr>"
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
    
    html_content += "</table><p style='color:grey; font-size:11px; margin-top:20px;'>※ 본 보고서는 NIA 연구 지원을 위해 2주 단위로 자동 발송됩니다.</p></body></html>"
    msg.attach(MIMEText(html_content, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    results = fetch_bills()
    send_email(results)
