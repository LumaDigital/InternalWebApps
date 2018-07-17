import smtplib
import socket
import time

mail_record = {}


def sent_mail_already(data):
    name = str(data['Name'])

    if name in mail_record:
        if mail_record[name] + 60 * 60 * 24 < time.time():

            # Lets send another mail
            mail_record[name] = time.time()
            return False

        else:
            # Too soon to send another mail
            return True

    else:
        mail_record[name] = time.time()
        return False



def send(data):

    if sent_mail_already(data):
        return

    local_ip = socket.gethostbyname(socket.gethostname())
    from_address = 'lumaanimation@gmail.com'
    to_address = 'martine@luma.co.za'

    username = 'lumaanimation@gmail.com'
    password = '$uperman1#'

    subject = "Server Temperature Warning"
    text = "Machine with Name: " + data['Name'] + " is running hot!"

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.login(username, password)

    message = 'Subject: {}\n\n{}'.format(subject, text)

    server.sendmail(from_address, to_address, message)
    server.quit()
