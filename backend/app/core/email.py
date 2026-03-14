import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

def send_email(to_email: str, subject: str, html_content: str):
    if not settings.SMTP_USERNAME:
        print(f"[EMAIL SKIP] To: {to_email} | Subject: {subject}")
        return
    msg = MIMEMultipart()
    msg["From"]    = settings.SMTP_FROM_EMAIL
    msg["To"]      = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)

def otp_email_html(otp: str, purpose: str = "Email Verification") -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:32px;background:#f8faff;border-radius:16px;">
      <div style="background:linear-gradient(135deg,#1e3a8a,#2563eb);padding:24px;border-radius:12px;text-align:center;margin-bottom:24px;">
        <h2 style="color:white;margin:0;">Production RAG System</h2>
      </div>
      <h3 style="color:#1e293b;">{purpose}</h3>
      <p style="color:#64748b;">Your one-time verification code is:</p>
      <div style="background:#2563eb;color:white;font-size:32px;font-weight:700;letter-spacing:8px;padding:20px;border-radius:12px;text-align:center;margin:20px 0;">
        {otp}
      </div>
      <p style="color:#94a3b8;font-size:13px;">This code expires in 10 minutes. Do not share it with anyone.</p>
    </div>
    """
