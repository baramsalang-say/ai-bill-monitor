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

def fetch_bills():
    # 의안목록전체 API
    url = "https://open.assembly.go.kr/portal/openapi/nzmimehqvxbmqvpif"
    
    # 22대 국회 개원 시점부터 현재까지 넉넉하게 설정
    date_limit = "20240530" 
    
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 500  # 한 번에 500건씩 확인
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # NIA 도메인 통합 키워드 (거의 모든 IT/데이터 관련 키워드 포함)
        keywords = [
            "인공지능", "AI", "데이터", "지능정보", "디지털", "알고리즘", "지능형", 
            "정보통신", "ICT", "클라우드", "소프트웨어", "플랫폼", "메타버스", 
            "가상융합", "로봇", "개인정보", "공공데이터", "컴퓨팅", "네트워크"
        ]
        
        filtered_bills = []
        service_name = 'nzmimehqvxbmqvpif'

        if service_name in data:
            rows = data[service_name][1].get('row', [])
            # [추가] 수집된 데이터를 제안일 기준으로 다시 한번 정렬
            rows.sort(key=lambda x: x.get('PROPOSE_DT', ''), reverse=True)
            
            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                raw_dt = b.get('PROPOSE_DT', '')
                ppsl_dt = raw_dt.replace("-", "") if raw_dt else ""
                
                # 22대 국회 이후 데이터 중 키워드 매칭
                if ppsl_dt and ppsl_dt >= date_limit:
                    clean_nm = bill_nm.upper().replace(" ", "")
                    if any(k.upper() in clean_nm for k in keywords):
                        filtered_bills.append({
                            'date': raw_dt,
                            'title': bill_nm,
                            'proposer': b.get('PROPOSER', ''),
                            'link': f"https://likms.assembly.go.kr/bill/billDetail.do?billId={b.get('BILL_ID')}"
                        })
        
        return filtered_bills
    except Exception as e:
        print(f"데이터 수집 에러: {e}")
        return []

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [NIA] 국회 지능정보사회 입법 동향 - {len(bills)}건 발견"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body style="font-family: 'Malgun Gothic', sans-serif;">
        <h2 style="color: #002d56; border-left: 5px solid #002d56; padding-left: 10px;">📊 국회 실시간 입법 동향 모니터링 (NIA)</h2>
        <p><b>조회 범위:</b> 제22대 국회 상정 의안 전체 대상</p>
    """
    if not bills:
        html += "<p style='color: #c0392b; font-weight: bold;'>현재 검색 조건에 부합하는 최근 상정 법안이 없습니다.</p>"
    else:
        html += f"<p>총 <b>{len(bills)}건</b>의 주요 법안이 감지되었습니다.</p>"
        html += "<table border='1' style='border-collapse: collapse; width: 100%; border: 1px solid #ddd; font-size: 13px;'>"
        html += "<tr style='background:#002d56; color: white;'><th>제안일</th><th>의안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:10px; text-align:center;'>{b['date']}</td><td style='padding:10px;'><a href='{b['link']}' style='font-weight:bold; color:#002d56;'>{b['title']}</a></td><td style='padding:10px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    
    html += "<p style='font-size: 11px; color: #888; margin-top: 20px;'>※ 본 리포트는 국회 오픈 API 데이터를 기반으로 2주 단위 자동 발송됩니다.</p></body></html>"

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
    print(f"이메일 발송 완료! (건수: {len(bills)})")

if __name__ == "__main__":
    results = fetch_bills()
    send_email(results)
