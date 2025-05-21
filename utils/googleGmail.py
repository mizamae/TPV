from django.core import mail
from django.conf import settings
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import os
import logging
logger = logging.getLogger("models")

# import ssl
# from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
# from django.utils.functional import cached_property

# class EmailBackend(SMTPBackend):
#     @cached_property
#     def ssl_context(self):
#         if self.ssl_certfile or self.ssl_keyfile:
#             ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
#             ssl_context.load_cert_chain(self.ssl_certfile,self.ssl_keyfile)
#             return ssl_context
#         else:
#             ssl_context = ssl.create_default_context()
#             ssl_context.check_hostname = False
#             ssl_context.verify_mode = ssl.CERT_NONE
#             return ssl_context

class googleGmail_handler(object):

    @staticmethod
    def attachment_data(attachment):
        try:
            with open(attachment, 'rb') as f:
                logo_data = f.read()
        except:
            logo_data = attachment
        logo = MIMEMultipart(logo_data)
        filename = str(os.path.basename(attachment)) # be carefull with the filename. It seems it does not work if "logo" is oncluded in the filename
        logo.add_header('Content-Disposition', 'attachment',filename=filename)
        return logo

    @staticmethod
    def sendEmail(subject,recipient,html_content,attachments=None):

        email = mail.EmailMessage(
                subject=subject,
                body=html_content,
                from_email=settings.EMAIL_HOST_USER,
                to=(recipient,),
                reply_to=[],
            )
        email.content_subtype = "html"

        if attachments:
            for attachment in attachments:
                if ".pdf" in attachment:
                    email.attach_file(attachment)
                else:
                    email.attach(googleGmail_handler.attachment_data(attachment))
        email.send()

        logger.info("Confirmation email sent to " + str(recipient))
    
    @staticmethod
    def sendMultipleEmails(subject,recipients,html_content,attachments=None):
        connection = mail.get_connection()
        emails=[]

        # this sends individual mails to each recipient so that does not disclose the addresses
        for recv in recipients:
            email = mail.EmailMessage(
                                            subject=subject,
                                            body=html_content,
                                            from_email=settings.EMAIL_HOST_USER,
                                            to=[recv,],
                                            bcc=[],
                                            reply_to=[],
                                            connection=connection,
                                        )
            email.content_subtype = "html"
            if attachments:
                for attachment in attachments:
                    if ".pdf" in attachment:
                        email.attach_file(attachment)
                    else:
                        email.attach(googleGmail_handler.attachment_data(attachment))
            emails.append(email)
               
        # Send the two emails in a single call -
        connection.send_messages(emails)
        # The connection was already open so send_messages() doesn't close it.
        # We need to manually close the connection.
        connection.close()

        logger.info("Notification email sent to " + str(recipients))