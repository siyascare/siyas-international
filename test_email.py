# test_email.py — alag file banao, run karo
import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Test email from Siyas app")
msg["Subject"] = "Test"
msg["From"] = "siyas.care@gmail.com"
msg["To"] = "siyas.care@gmail.com"   # apne aap ko bhejo

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login("siyas.care@gmail.com", "wwcpuneoxajjeijw")
    server.sendmail("siyas.care@gmail.com", "siyas.care@gmail.com", msg.as_string())

print("Email sent!")