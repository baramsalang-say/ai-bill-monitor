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

# [필터링 키워드]
KEYWORDS = ["인공지능", "AI", "알고리즘", "데이터", "딥러닝", "머신러닝", "지능정보", "챗GPT", "자동화"]

def fetch_bills():
    # 제22대 국회를 포함한 최신 의안 통합 API 주소로 변경 (가장 확실한 소스)
    # pSize를 1000으로 늘려 최근 1년치를 충분히 커버합니다.
    url = f"https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu?KEY={API_KEY}&Type=json&pIndex=1&pSize=1000"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # 1년 전 날짜 설정
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # API 응답 구조 확인 및 데이터 추출
        if 'nwvrqwxyaytdsfvhu' in data:
            rows = data['nwvrqwxyaytdsfvhu'][1].get('row', [])
            
            filtered = []
            for b in rows:
                bill_name = b.get('BILL_NM', '')
                propose_dt = b.get('PROPOSE_DT', '') # 제안일
                
                # 1. 날짜 필터 (최근 1년)
                if propose_dt and propose_dt >= one_year_ago:
                    # 2. 키워드 필터 (띄어쓰기 무시 매칭)
                    clean_bill_name = bill_name.upper().replace(" ", "")
                    if any(k.upper() in clean_bill_name for k in KEYWORDS):
                        filtered.append(b)
            
            filtered.sort(key=lambda x: x['PROPOSE_DT'], reverse=True)
            return filtered
        else:
            print("API 응답 구조가 예상과 다릅니다. 주소를 다시 확인하세요.")
            return []
    except Exception as e:
        print(f"데이터 수집 중 오류 발생: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[긴급교정] 국회 AI 관련 법안 모니터링 - {len(bills)}건 발견 ({datetime.now().strftime('%Y-%m-%d')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html_content = f"""
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: 'Malgun Gothic', sans-serif; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #004792; color: white; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .link-btn {{ color: #004792; text-decoration: none; font-weight: bold; }}
            .header-info {{ background-color: #f0f4f8; padding: 15px; border-left: 5px solid #004792; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <h2 style="color: #2c3e50;">🏛️ 제22대 국회 AI 관련 법안 모니터링</h2>
        <div class="header-info">
            <b>조회 기준:</b> 최근 1년 (제22대 국회 포함)<br>
            <b>검색 결과:</b> 총 {len(bills)}건이 발견되었습니다.
        </div>
        <table>
            <tr>
                <th style="width: 120px;">제안일</th>
                <th>의안명</th>
                <th style="width: 150px;">제안자</th>
                <th style="width: 100px;">링크</th>
            </tr>
    """
    
    if not bills:
        html_content += "<tr><td colspan='4' style='text-align: center; padding: 30px;'>최근 1년 내 해당 키워드로 상정된 의안이 없습니다.</td></tr>"
    else:
        for b in bills:
            bill_id = b.get('BILL_ID', '')
            # 22대 국회 상세 페이지 링크 생성
            link = f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
            
            html_content += f"""
            <tr>
                <td>{b['PROPOSE_DT']}</td>
                <td><b>{b['BILL_NM']}</b></td>
                <td>{b['PROPOSER']}</td>
                <td><a href="{link}" class="link-btn">상세보기</a></td>
            </tr>
            """
    
    html_content += """
        </table>
        <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">본 메일은 NIA 업무 지원을 위해 자동 생성된 보고서입니다.</p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MY_EMAIL, EMAIL_PW)
            server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
        print(f"발송 완료: {len(bills)}건")
    except Exception as e:
        print(f"메일 발송 에러: {e}")

if __name__ == "__main__":
    found_bills = fetch_bills()
    send_email(found_bills)
