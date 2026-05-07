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

# 모니터링 키워드 리스트
MONITORING_KEYWORDS = [
    "인공지능", "AI", "데이터", "디지털", "지능정보", "ICT", "정보통신", 
    "플랫폼", "알고리즘", "클라우드", "소프트웨어", "SW", "반도체", 
    "네트워크", "5G", "6G", "메타버스", "사이버", "보안", "양자"
]

def fetch_nia_specialized_bills():
    url = "https://open.assembly.go.kr/portal/openapi/BILLRCP"
    params = {
        'Key': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 1000 
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        filtered_bills = []
        # 한국 시각 기준으로 90일 전 계산 (조회 시작일)
        kst_now = datetime.now() + timedelta(hours=9)
        start_date_dt = kst_now - timedelta(days=90)
        
        start_date_str = start_date_dt.strftime('%Y-%m-%d') # 필터링용 (YYYY-MM-DD)

        if 'BILLRCP' in data:
            rows = data['BILLRCP'][1].get('row', [])
            for b in rows:
                bill_nm = b.get('BILL_NM', '')
                ppsl_dt = b.get('PPSL_DT', '')
                
                # 날짜 필터: 90일 전보다 이전 데이터는 건너뜀
                if ppsl_dt < start_date_str:
                    continue
                
                clean_nm = bill_nm.upper().replace(" ", "")
                if any(k.upper() in clean_nm for k in MONITORING_KEYWORDS):
                    filtered_bills.append({
                        'date': ppsl_dt,
                        'title': bill_nm,
                        'proposer': b.get('PPSR_NM', '의원 등'),
                        'link': b.get('LINK_URL', '')
                    })
        return filtered_bills, start_date_dt, kst_now
    except Exception as e:
        print(f"데이터 가져오기 오류: {e}")
        return [], None, None

def send_nia_report(bills, start_dt, end_dt):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🤖 [모니터링] 인공지능 및 디지털 관련 입법 리포트 ({len(bills)}건)"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    # 날짜 표기 형식 변환 (yy.mm.dd)
    start_fmt = start_dt.strftime('%y.%m.%d')
    end_fmt = end_dt.strftime
