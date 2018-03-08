import smtplib
import socket


def send():

    local_ip = socket.gethostbyname(socket.gethostname())
    from_address = 'johanhvanstaden@gmail.com'
    to_address = 'johanhvanstaden@gmail.com'

    username = 'johanhvanstaden'
    password = 'wqljpjyilfuvabku'

    subject = "Server Temperature Warning"
    text = "Machine with IP address: " + local_ip + " shutting down"

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.login(username, password)

    message = 'Subject: {}\n\n{}'.format(subject, text)

    server.sendmail(from_address, to_address, message)
    server.quit()
