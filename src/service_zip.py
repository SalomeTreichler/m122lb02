import logging
import time
import coloredlogs

import autoparser
import cache
import config
import network


def main():
    open_invoices = cache.get_invoice_numbers()
    network.download_receipts(config.get_server_config(config.Server.PAYMENT), open_invoices, process_receipt)


def process_receipt(receipt_name: str, receipt: str, invoice_number: str) -> bool:
    """Processes a receipt

    1) Get save receipt
    2) Zip both files
    3) Send email with Zip
    4) Upload ZIP to customer server

    args:
        receipt_name (str): Receipt file name
        receipt (str): Receipt content
        invoice_number (str): Number of the invoice

    returns:
        (bool): If receipt got processed successfully
    """
    # Get invoice for receipt and exit if there is none
    invoice_file_name = cache.get_invoice_by_number(invoice_number)
    if not invoice_file_name:
        return False

    # Get required data for email
    receipt_date, receipt_time = get_receipt_time_date(receipt_name)
    try:
        receiver_name, receiver = autoparser.get_email_receiver(
            cache.read(invoice_file_name.replace(".txt", ".data")).encode('utf-8'))
    except FileNotFoundError:
        logging.error(f"Failed to get data file for receipt {receipt_name}")
        return False

    # Cache current receipt as Kxxx_xxxxx_receipt.txt
    receipt_file_name = invoice_file_name.replace("invoice", "receipt")
    cache.write(receipt_file_name, receipt)
    logging.info(f"Cached file {receipt_file_name}")

    # Cache ZIP as Kxxx_xxxxx.zip
    zip_file_name = invoice_file_name.replace("_invoice.txt", ".zip")
    cache.zip_files(invoice_file_name, receipt_file_name, zip_file_name)
    logging.info(f"Cached file {zip_file_name}")

    # Send mail to client
    network.send_mail(
        config.get_email_sender(), config.get_email_sender_name(),
        receiver, receiver_name,
        invoice_number, receipt_date,
        receipt_time, zip_file_name)
    logging.info(f"Sent email to '{receiver}' for invoice '{invoice_number}'")

    # Upload file to customer server again
    network.upload_file(config.get_server_config(config.Server.CUSTOMER), zip_file_name,
                        cache.read_binary(zip_file_name))
    logging.info(f"Uploaded file {zip_file_name} to {config.get_server_config(config.Server.CUSTOMER).hostname}")

    cache.clear(invoice_number)
    logging.info(f"Cleared cache files {invoice_number}")

    return True


def get_receipt_time_date(receipt_name: str):
    """Get time from receipt file name

    args:
        receipt_name (str): Name of the receipt
    returns:
        date (str), time (str): Time and date formatted like provided in config
    """
    email_date_format = config.get_date_email_format()
    email_time_format = config.get_time_email_format()

    file_date_format = config.get_date_file_format()
    file_time_format = config.get_time_file_format()

    receipt_date = time.strftime(
        email_date_format, time.strptime(
            receipt_name[13:].split("_")[0], file_date_format))
    receipt_time = time.strftime(
        email_time_format, time.strptime(
            receipt_name[13:].split("_")[1].replace(".txt", ""), file_time_format))

    return receipt_date, receipt_time


def logging_init():
    """Initialize logging

    Specifies which file to use for logging and sets color logging
    for better comprehension
    """
    logging.basicConfig(level=logging.DEBUG)
    coloredlogs.install()


if __name__ == "__main__":
    logging_init()
    main()
