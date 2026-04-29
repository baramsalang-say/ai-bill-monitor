import requests
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText

# [보안 설정] GitHub Secrets에서 값을 가져옵니다.
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"  # <--- 본인 이메일로 수정하세요!

# [필터링 설정] 감시할 키워드
KEYWORDS = ["인공지능", "AI", "알고리즘", "데이터", "딥러닝", "머신러닝"]

def fetch_bills():
    # [테스트 모드] 일단 메일이 오는지 확인하기 위해 넉넉하게 최근 100일치를 조회합니다.
    start_date = (datetime.now() - timedelta(days=100)).strftime('%Y%m%d')
    
    url = f"https://open.assembly.go.kr/portal/openapi/nzmimehqvxbmqvpif?KEY={API_KEY}&Type=json&pIndex=1&pSize=100&PROPOSE_DT={start_date}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if 'nzmimehqvxbmqvpif' in data:
            rows = data['nzmimehqvxbmqvpif'][1].get('row', [])
            # 키워드 필터링
            filtered = [b for b in rows if any(k.upper() in b['BILL_NM'].upper().replace(" ", "") for k in KEYWORDS)]
            return filtered
        return []
    except Exception as e:
        print(f"데이터 수집 중 오류 발생: {e}")
        return []

def send_email(bills):
    if not bills:
        # 테스트 시 데이터가 없을 경우를 대비해 안내 메일이라도 보냅니다.
        content = "최근 100일간 검색된 AI 관련 법안이 없습니다. 시스템은 정상 작동 중입니다."
    else:
        content = f"최근 상정된 AI 관련 주요 법안 리스트입니다. (총 {len(bills)}건)\n\n"
        for b in bills:
            content += f"▶ 법안명: {b['BILL_NM']}\n"
            content += f"   - 제안자: {b['PROPOSER']}\n"
            content += f"   - 제안일: {b['PROPOSE_DT']}\n"
            content += f"   - 링크: {b.get('DETAIL_LINK', '정보 없음')}\n\n"
    
    msg = MIMEText(content)
    msg['Subject'] = f"[테스트] 국회 법안 모니터링 시스템 작동 확인"
    msg['From'] = MY_EMAIL
    msg['To'] = "jyjeong@nia.or.kr"
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MY_EMAIL, EMAIL_PW)
            server.sendmail(MY_EMAIL, "jyjeong@nia.or.kr", msg.as_string())
        print("이메일 발송 완료!")
    except Exception as e:
        print(f"이메일 발송 중 오류 발생: {e}")

if __name__ == "__main__":
    found_bills = fetch_bills()
    send_email(found_bills)
