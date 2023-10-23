import os
import shutil
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

from plasticome.config.celery_config import celery_app

load_dotenv(override=True)


@celery_app.task
def send_email_with_results(result: tuple, user_data: dict):

    smtp_server = os.getenv('MAIL_SERVER')
    smtp_sender = os.getenv('MAIL_USER')
    smtp_password = os.getenv('MAIL_SECRET')
    smtp_port = os.getenv('MAIL_ACCESS_PORT')

    msg = MIMEMultipart()
    msg['From'] = smtp_sender
    msg['To'] = user_data.get('user_email', False)
    msg[
        'Subject'
    ] = '[🍄 PLASTICOME]: Resultados da Análise de Enzimas para Degradação de Plásticos'

    result_path, negative_result = result
    body = f'Olá {user_data.get("user_name", "Usuário plasticome")}, Trouxe informações referentes à análise do fungo: {user_data.get("organism_name", "<Erro ao buscar nome>")}-{user_data.get("genbank_id", "Genbank id não disponível")}\n'
    if negative_result:
        body = f'{body}\n{negative_result}\n\n[🍄 PLASTICOME by G2BC]'
    else:
        with open(result_path, 'rb') as image_file:
            result_image = MIMEImage(image_file.read())
            msg.attach(result_image)
        body = f'{body}\nSegue em anexo o resultado da sua análise de enzimas em relação à degradação de plásticos via plasticome. Lembre-se que essa análise aponta enzimas tem uma POSSIBILIDADE de degradação com os plásticos relacionados.\n\n[🍄 PLASTICOME by G2BC]'

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_sender, smtp_password)
        server.sendmail(
            smtp_sender, user_data.get('user_email', False), msg.as_string()
        )
        server.quit()
        absolute_dir = os.path.dirname(result_path)
        shutil.rmtree(absolute_dir)
        return True, False
    except Exception as e:
        return False, f'Erro ao enviar e-mail: {e}'
