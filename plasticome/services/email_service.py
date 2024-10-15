import os
import shutil
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

from plasticome.config.celery import celery_app

load_dotenv(override=True)


@celery_app.task
def send_email_with_results(results: tuple, user_data: dict):

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

    results_path, negative_result, error = results
    if error:
        return False, error

    body = f'Olá {user_data.get("user_name", "Usuário plasticome")},\n Seguem informações referentes à análise do fungo: {user_data.get("organism_name", "<Erro ao buscar nome do fungo>")}-{user_data.get("genbank_id", "Genbank id não disponível")}\n'
    if negative_result:
        body = f'{body}\n{negative_result}\n\n[🍄 PLASTICOME by G2BC]'
    else:
        graphic_result = os.path.join(results_path, 'plasticome_result.png')
        blast_align_result = os.path.join(results_path, 'blast_align.csv')

        with open(graphic_result, 'rb') as image_file:
            result_image = MIMEImage(image_file.read())
            msg.attach(result_image)

        with open(blast_align_result, 'rb') as csv_file:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(csv_file.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{os.path.basename(blast_align_result)}"',
            )
            msg.attach(part)

        body = f"""{body}
        Informações da análise:
            - A análise aponta enzimas com possibilidade de degradação de plásticos.
            - O gráfico mostra quais enzimas têm possibilidade de degradação e seus tipos de plástico relacionados.
            - A análise de similaridade compara as enzimas encontradas com enzimas de degradação comprovada.
        Lembre-se que esses resultados são indicativos!
        Anexos:
            1. Gráfico de Relação Enzima-Plástico
            2. Planilha com Resultados Detalhados de Similaridade


        Esperamos que essa análise seja útil para você!
        [🍄 PLASTICOME by G2BC]
        """

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_sender, smtp_password)
        server.sendmail(
            smtp_sender, user_data.get('user_email', False), msg.as_string()
        )
        server.quit()
        absolute_dir = os.path.dirname(results_path)
        shutil.rmtree(absolute_dir)
        return True, False
    except Exception as e:
        return False, f'Erro ao enviar e-mail: {str(e)}'
