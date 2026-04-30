import requests
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [환경 변수] GitHub Secrets에서 가져오기
API_KEY = os.environ.get("ASSEMBLY_API_KEY")
EMAIL_PW = os.environ.get("MY_EMAIL_PW")
MY_EMAIL = "baramsalang@gmail.com"
RECEIVE_EMAIL = "jyjeong@nia.or.kr"

def fetch_bills():
    # 명세서(image_3628c4.png)에 정의된 의안정보 통합 API 주소
    url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
    
    # 최근 60일치 데이터를 수집 대상으로 설정
    date_limit = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
    keywords = ["인공지능", "AI", "데이터", "지능정보", "디지털", "알고리즘", "지능", "로봇"]
    
    filtered_bills = []
    
    print(f"조회 시작일 기준: {date_limit}")
    
    # 데이터 누락 방지를 위해 최대 1,000건(100건씩 10페이지)을 훑습니다.
    for page in range(1, 11):
        params = {
            'KEY': API_KEY,
            'Type': 'json',
            'pIndex': page,
            'pSize': 100
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            # [디버깅 로그] API가 데이터를 주는지 실시간 확인
            if page == 1:
                print("===== API 응답 첫 300자 샘플 =====")
                print(response.text[:300])
                print("================================")

            if 'nwvrqwxyaytdsfvhu' in data:
                rows = data['nwvrqwxyaytdsfvhu'][1].get('row', [])
                if not rows: break # 더 이상 데이터가 없으면 중단
                
                for b in rows:
                    bill_nm = b.get('BILL_NM', '')
                    # 날짜 형식(2026-04-30 or 20260430) 보정
                    raw_dt = b.get('PPSL_DT', '')
                    ppsl_dt = raw_dt.replace("-", "").replace(".", "") if raw_dt else ""
                    
                    ppsr_nm = b.get('PPSR_NM', '')
                    bill_id = b.get('BILL_ID', '')

                    # 1. 날짜 조건 확인 (최근 60일)
                    if ppsl_dt and ppsl_dt >= date_limit:
                        # 2. 키워드 조건 확인 (대소문자/띄어쓰기 무시)
                        clean_nm = bill_nm.upper().replace(" ", "")
                        if any(k.upper() in clean_nm for k in keywords):
                            filtered_bills.append({
                                'date': raw_dt, 
                                'title': bill_nm,
                                'proposer': ppsr_nm,
                                'link': f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
                            })
                
                # 가져온 데이터의 마지막 날짜가 이미 기준일보다 한참 전이면 다음 페이지 안 봐도 됨
                if rows[-1].get('PPSL_DT', '').replace("-", "") < date_limit:
                    break
            else:
                print(f"{page}페이지: 데이터를 찾을 수 없습니다. (RESULT: {data.get('RESULT')})")
                break
                
        except Exception as e:
            print(f"오류 발생: {e}")
            break
            
    # 중복 제거 및 최신순 정렬
    unique_bills = {b['link']: b for b in filtered_bills}.values()
    return sorted(unique_bills, key=lambda x: x['date'], reverse=True)

def send_email(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ [NIA] 국회 입법 동향 리포트 - {len(bills)}건 발견 ({datetime.now().strftime('%m/%d')})"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    html = f"""
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: 'Malgun Gothic', sans-serif; font-size: 13px; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background-color: #004792; color: white; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .link-btn {{ color: #004792; font-weight: bold; text-decoration: none; }}
        </style>
    </head>
    <body>
        <h2>📊 NIA 지능정보사회 입법 동향 보고</h2>
        <p>최근 60일간 상정된 의안 1,000건을 전수조사한 실시간 결과입니다.</p>
    """

    if not bills:
        html += "<p style='color: #e74c3c; font-weight: bold;'>조회 기간 내 조건에 맞는 새로운 법안이 발견되지 않았습니다.</p>"
    else:
        html += "<table><tr><th>제안일</th><th>법안명</th><th>제안자</th><th>상세보기</th></tr>"
        for b in bills:
            html += f"""
            <tr>
                <td>{b['date']}</td>
                <td><b>{b['title']}</b></td>
                <td>{b['proposer']}</td>
                <td><a href='{b['link']}' class='link-btn'>원문 보기</a></td>
            </tr>
            """
        html += "</table>"
    
    html += "<p style='font-size: 11px; color: #777; margin-top: 20px;'>※ 본 보고서는 국회 오픈 API 데이터를 바탕으로 NIA 업무 지원을 위해 자동 발송됩니다.</p></body></html>"

    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MY_EMAIL, EMAIL_PW)
            server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
        print("메일 발송 성공")
    except Exception as e:
        print(f"메일 발송 에러: {e}")

if __name__ == "__main__":
    results = fetch_bills()
    send_email(results)
