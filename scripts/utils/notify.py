import smtplib
import os

EMAIL_ADDRESS = os.environ.get('EMAIL_ADDR')
EMAIL_PASSWORD = os.environ.get('EMAIL_ACCESS_TOKEN')

def notify(to,sub,msg):
    print('Sending an email with subject:',sub)
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.ehlo()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        message = f"Subject: {sub}\n{msg}"
        smtp.sendmail(EMAIL_ADDRESS, to, message)