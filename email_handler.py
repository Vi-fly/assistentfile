import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_task_email(recipient_email, subject, message):
    sender_email = "myhw765@gmail.com"
    sender_password = "airukqfciidluzzm"

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        print(f"Email sent to {recipient_email}")
    except smtplib.SMTPAuthenticationError:
        print("Error: Authentication failed. Check your email and password.")
    except smtplib.SMTPException as e:
        print(f"Error: Failed to send email. {e}")
    finally:
        server.quit()