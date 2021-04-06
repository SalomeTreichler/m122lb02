import ftplib
import io
import logging
import re
import smtplib
import ssl
import string
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

import cache
import config


def download_invoices(server_config: config.ServerConfig, callback) -> None:
    """Downloads invoices from server

    args:
        server_config (config.ServerConfig): Credentials for server
        callback (Callable[[str]]): Callback to process one file
    """
    try:
        logging.info(f"Connecting to server {server_config.hostname}")
        file_list = _list_files(server_config, config.get_invoice_pattern())
        with ftplib.FTP(server_config.hostname) as conn:
            conn.login(server_config.username, server_config.password)
            conn.cwd(server_config.files_out)
            for invoice_name in file_list:
                with io.BytesIO() as buffer_io:
                    conn.retrbinary(f"RETR {invoice_name}", buffer_io.write)
                    invoice_content = buffer_io.getvalue()
                logging.info(f"Downloaded invoice {invoice_name}")
                logging.info(f"Processing invoice {invoice_name}")
                if callback(invoice_name, invoice_content):
                    _del_file(server_config, server_config.files_out, invoice_name)
                    logging.info(f"Deleted invoice {invoice_name}")
    except ftplib.error_perm as e:
        logging.fatal(f"Server error: {e}")
        exit(0)


def download_receipts(server_config: config.ServerConfig, open_invoice_nrs: List[str], callback):
    """Download receipt based on pending invoices

    args:
        server_config (config.ServerConfig): Credentials for server
        open_invoice_nrs (List[str]): Cached and pending invoice numbers
        callback (Callable): Callback to process receipt
    """
    try:
        logging.info(f"Connecting to server {server_config.hostname}")
        file_list = _list_files(server_config, config.get_receipt_pattern())
        with ftplib.FTP(server_config.hostname) as conn:
            conn.login(server_config.username, server_config.password)
            conn.cwd(server_config.files_out)
            for receipt_name in file_list:
                # Go through receipt and search for matching invoice number
                with io.BytesIO() as buffer_io:
                    conn.retrbinary(f"RETR {receipt_name}", buffer_io.write)
                    receipt_content = buffer_io.getvalue().decode('utf-8')
                for open_invoice_nr in open_invoice_nrs:
                    if open_invoice_nr in receipt_content:
                        # Delete and process receipt
                        logging.info(f"Downloaded receipt {receipt_name}")
                        logging.info(f"Processing receipt {receipt_name}")
                        if callback(receipt_name, receipt_content, open_invoice_nr):
                            _del_file(server_config, server_config.files_out, receipt_name)
                            logging.info(f"Deleted receipt {receipt_name}")
                        break
                    else:
                        logging.info(f"Ignored receipt {receipt_name}")
    except ftplib.error_perm as e:
        logging.fatal(f"Server error: {e}")
        exit(0)


def upload_file(server_config: config.ServerConfig, filename: str, content: bytes) -> None:
    """Upload file to server

    args:
        server_config (config.ServerConfig): Credentials for server
        filename (str): Name of the new file on the server
        content (str): Content of the new file
    """
    try:
        logging.info(f"Connecting to server {server_config.hostname}")
        output = io.BytesIO(content)

        with ftplib.FTP(server_config.hostname) as conn:
            conn.login(server_config.username, server_config.password)
            conn.cwd(server_config.files_in)
            conn.storbinary(f"STOR {filename}", output)
        logging.info(f"Uploaded file {filename} to {server_config.hostname}")
        logging.info(f"Disconnecting from server {server_config.hostname}")
    except ftplib.error_perm as e:
        logging.fatal(f"Server error: {e}")
        exit(0)


def _del_file(server_config: config.ServerConfig, path: str, filename: str) -> None:
    """Delete file from server

    args:
        server_config (config.ServerConfig): Credentials for server
        path (str): Path to the file to delete e.g. AP17bGribi/in
        filename (str): Name of the file to delete
    """
    try:
        with ftplib.FTP(server_config.hostname) as conn:
            conn.login(server_config.username, server_config.password)
            conn.cwd(path)
            conn.delete(filename)
    except ftplib.error_perm as e:
        logging.fatal(f"Server error: {e}")
        exit(0)


def _list_files(server_config: config.ServerConfig, regex_pattern: str) -> List[str]:
    """List files in a certain directory on server that match a certain regex pattern

    args:
         server_config (config.ServerConfig): Credentials for server
         regex_pattern (str): Regex pattern that files have to match

    returns:
        List[str]: Filenames of matching files
    """
    try:
        with ftplib.FTP(server_config.hostname) as conn:
            conn.login(server_config.username, server_config.password)
            conn.cwd(server_config.files_out)
            file_list = list(filter(
                lambda i: re.match(regex_pattern, i) and
                          re.match(regex_pattern, i).string == i,
                conn.nlst()))

            if not file_list:
                logging.info(f"No files found on {server_config.hostname} that match '{regex_pattern}'")
            return file_list
    except ftplib.error_perm as e:
        logging.fatal(f"Server error: {e}")
        exit(0)


def send_mail(sender: str, sender_name: str,
              receiver: str, receiver_name: str,
              invoice_number: str, receipt_date: str,
              receipt_time: str, zip_file_name: str):
    """Sends an email with an attached zip to the customer

    args:
        invoice_number (str): Number of the invoice
        zip_file_name (str): Name of the zip file
    """
    message = string.Template(open(config.get_mail_template()).read()).substitute(
        receiver_name=receiver_name, sender_name=sender_name,
        invoice_number=invoice_number,
        time=receipt_time, date=receipt_date,
        server=config.get_server_config(config.Server.PAYMENT).hostname)

    email_settings = config.get_server_config(config.Server.EMAIL)
    with smtplib.SMTP_SSL(email_settings.hostname, 465, context=ssl.create_default_context()) as server:
        server.login(email_settings.username, email_settings.password)

        mail = MIMEMultipart()
        mail['From'] = f"{sender_name} <{sender}>"
        mail['To'] = f"{receiver_name} <{receiver}>"
        mail['Subject'] = f"Erfolgte Verarbeitung Rechnung {invoice_number}"
        mail.attach(MIMEText(message, 'plain'))

        zip_attachment = MIMEBase('application', "octet-stream")
        zip_attachment.set_payload(cache.read_binary(zip_file_name))
        encoders.encode_base64(zip_attachment)
        zip_attachment.add_header('Content-Disposition', f'attachment; filename="{zip_file_name}"')

        mail.attach(zip_attachment)

        server.sendmail(sender, receiver, mail.as_string())
