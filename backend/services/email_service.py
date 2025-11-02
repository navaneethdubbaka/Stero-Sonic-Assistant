import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional

class EmailService:
    def __init__(self):
        self.email = os.getenv("EMAIL_ADDRESS", "")
        self.password = os.getenv("EMAIL_PASSWORD", "")
    
    def send_email(self, to: str, content: str, attachment_path: Optional[str] = None) -> dict:
        """Send email with optional attachment"""
        try:
            if not self.email or not self.password:
                return {"success": False, "error": "Email credentials not configured"}
            
            # Set up the server
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email, self.password)
            
            # Set up the MIME
            message = MIMEMultipart()
            message['From'] = self.email
            message['To'] = to
            message['Subject'] = "Automated Email from Stereo Sonic"
            
            # Attach the body
            message.attach(MIMEText(content, 'plain'))
            
            # Attach file if provided
            if attachment_path and os.path.isfile(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(attachment_path)}'
                    )
                    message.attach(part)
            
            # Send the message
            text = message.as_string()
            server.sendmail(self.email, to, text)
            server.quit()
            
            return {"success": True, "message": "Email sent successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

