import logging
import time
import ssl
import smtplib
from trisigma.infra.common import files

class SMTPHandler(logging.StreamHandler):

    def __init__(self, creds_host, creds_user, default_receiver, port=465, smtphost="smtp.gmail.com"):
        credentials = files.get_credentials(creds_host, creds_user)
        self.usr = credentials["username"]
        self.pwd = credentials["password"]
        self.receiver = default_receiver
        self.port = port
        self.smtp_host = smtphost
        self.max_volume = 10
        self.cooldown = 180
        self.emits = []
        super().__init__()

    def emit(self, record):
        try:
            if not self.limit_reached():
                msg = self.format(record)
                self.send(msg, "", self.receiver)
                self.emits.append(time.time())
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def limit_reached(self):
        if len(self.emits) < self.max_volume:
            return False
        else:
            if (time.time() - self.emits[0]) > self.cooldown:
                self.emits.pop(0)
                return False
            else:
                return True

    def send (self, subj, body, receiver):
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp_host, self.port, context=context) as server:
            server.login(self.usr, self.pwd)
            message = """
            Subject: %s

            %s""" % (subj, body)
            server.sendmail(self.usr, receiver, message)
