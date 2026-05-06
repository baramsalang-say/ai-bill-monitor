# monitor.py의 상단 import 문에 timedelta 추가 확인
from datetime import datetime, timedelta

# ... (중략) ...

def send_nia_report(bills):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🤖 [모니터링] 인공지능 및 디지털 관련 입법 리포트 ({len(bills)}건)"
    msg['From'] = MY_EMAIL
    msg['To'] = RECEIVE_EMAIL

    # [교정] UTC 시간을 한국 시각(KST, +9시간)으로 변환
    kst_now = datetime.now() + timedelta(hours=9)
    current_time_str = kst_now.strftime('%Y-%m-%d %H:%M')

    keyword_str = ", ".join(MONITORING_KEYWORDS)

    html = f"""
    <html><body style="font-family: 'Malgun Gothic', sans-serif; line-height: 1.6;">
        <h2 style="color: #1a73e8; border-left: 4px solid #1a73e8; padding-left: 10px;">인공지능 및 디지털 관련 입법 모니터링</h2>
        <p>최근 <b>3개월(90일)</b> 동안 접수된 의안 중 인공지능 및 디지털 관련 법안입니다.<br>
        총 <b>{len(bills)}건</b>의 의안이 자동 검색되었습니다.</p>
        
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px; font-size: 13px; color: #555;">
            <strong>🔍 검색 키워드:</strong> {keyword_str}
        </div>
    """
    
    if not bills:
        html += "<p style='color: #666;'>현재 해당 기간 내 조건과 일치하는 신규 법안이 없습니다.</p>"
    else:
        html += "<table border='1' style='border-collapse: collapse; width: 100%; border-color: #e0e0e0;'>"
        html += "<tr style='background:#f1f3f4;'><th>접수일</th><th>의안명</th><th>제안자</th></tr>"
        for b in bills:
            html += f"<tr><td style='padding:10px; text-align:center; font-size: 13px;'>{b['date']}</td><td style='padding:10px;'><a href='{b['link']}' style='font-weight:bold; color:#1a73e8; text-decoration: none;'>{b['title']}</a></td><td style='padding:10px; text-align:center; font-size: 13px;'>{b['proposer']}</td></tr>"
        html += "</table>"
    
    html += f"""
        <p style="margin-top: 20px; font-size: 11px; color: #999;">본 메일은 국회 Open API를 통해 자동 생성되었습니다. (발송시각: {current_time_str} KST)</p>
    </body></html>
    """
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MY_EMAIL, EMAIL_PW)
        server.sendmail(MY_EMAIL, RECEIVE_EMAIL, msg.as_string())
