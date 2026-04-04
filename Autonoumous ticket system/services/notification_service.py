import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, ESCALATION_EMAIL

def send_escalation_email(title, description, decision, user_role):

    subject = f"Escalated IT Support Ticket - {decision['category']}"

    body = f"""

Dear IT Support Team,

Ticket Details
Reported By Role : {user_role}
Category         : {decision['category']}
Priority Level   : {decision['priority']}

Ticket Title
{title}

Issue Description
{description}

Suggested Resolution
{decision['suggested_resolution']}

Action Required
This issue requires immediate attention from the IT support team. 
Please investigate and resolve the problem at the earliest.

"""

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = ESCALATION_EMAIL
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()

        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        server.sendmail(
            SENDER_EMAIL,
            ESCALATION_EMAIL,
            msg.as_string()
        )

        server.quit()

        print("Escalation email sent successfully")

    except Exception as e:
        print("Error sending email:", e)

        