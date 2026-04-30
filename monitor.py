import requests
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 환경 변수 세팅 (GitHub Secrets에 등록된 키를 사용합니다)
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def fetch_bills_test():
    # 최신 의안 접수 현황 API 주소
    url = "https://open.assembly.go.kr/portal/openapi/BILLRCPV2"
    
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 100 # 테스트용으로 최근 100건만 확인
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # [테스트용 광범위 키워드] 무엇이라도 걸리게끔 일반적인 단어를 넣었습니다.
        test_keywords = ["법률", "개정", "의안", "국회", "정부", "국가", "조세", "관리"]
        filtered_bills = []

        if 'BILLRCPV2' in data:
            rows = data['BILLRCPV2'][1].get('row', [])
            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                # 키워드 매칭 테스트
                clean_nm = bill_nm.replace(" ", "")
                if any(k in clean_nm for k in test_keywords):
                    filtered_bills.append({
                        'date': b.get('PPSL_DT', ''),
                        'title': bill_nm,
                        'proposer': b.get('PPSR_NM', '의원 등'),
                        'link': b.get('LINK_URL', '')
                    })
        return filtered_bills
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        return []

def send_test_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🧪 [시스템 테스트] 국회 데이터 수집 확인 ({len(bills)}건 발견)"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html><body style="font-family: 'Malgun Gothic', sans-serif;">
        <h2 style="color: #d35400;">⚠️ 시스템 정상 작동 테스트 리포트</h2>
        <p>이 메일은 API가 데이터를 정상적으로 가져오는지 확인하기 위해 <b>광범위 키워드</b>를 적용한 결과입니다.</p>
    """
    if not bills:
        html += "<p style='color: red; font-weight: bold;'>광범위 키워드에도 불구하고 0건입니다. API 권한을 재점검해야 합니다.</p>"
    else:
        html += f"<p>현재 API가 <b>{len(bills)}건</b>의 데이터를 성공적으로 수집하고 있습니다.</p>"
        html += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        html += "<tr style='background:#f39c12; color: white;'><th>접수일</th><th>의안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:8px; text-align:center;'>{b['date']}</td><td style='padding:8px;'>{b['title']}</td><td style='padding:8px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    html += "</body></html>"

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())

if __name__ == "__main__":
    results = fetch_bills_test()
    send_test_email(results)
