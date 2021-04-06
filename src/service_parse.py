import logging
import coloredlogs

import autoparser
import cache
import config
import network


def main():
    network.download_invoices(config.get_server_config(config.Server.CUSTOMER), process_invoice)


def process_invoice(invoice_file_name: str, invoice_content: bytes) -> bool:
    """Processes an invoice

        1) Cache data receipt
        2) Parse TXT and XML receipt
        3) Cache TXT receipt
        4) Upload XML to payment server

        args:
            invoice_file_name (str): Invoice file name
            invoice_content (bytes): Invoice content

        returns:
            (bool): If invoice got processed successfully
        """
    # Parse both XML and TXT files
    try:
        txt_file_name, txt_file_content = autoparser.parse_text(invoice_content)
        logging.info(f"Parsed file {txt_file_name} with auto-parser")
        xml_file_name, xml_file_content = autoparser.parse_xml(invoice_content)
        logging.info(f"Parsed file {xml_file_name} with auto-parser")
    except IndexError as e:
        logging.error(f"Failed to process invoice {invoice_file_name}: {e}")
        logging.info(f"Skipped invoice {invoice_file_name}")
        return False

    # Cache data file for later usage
    data_file_name = txt_file_name.replace(".txt", ".data")
    cache.write(data_file_name, invoice_content.decode('utf-8'))
    logging.info(f"Cached file {data_file_name}")

    # Cache TXT file to ZIP later
    cache.write(txt_file_name, txt_file_content)
    logging.info(f"Cached file {txt_file_name}")

    # Upload XML and TXT files to the payment server
    network.upload_file(config.get_server_config(config.Server.PAYMENT), xml_file_name, xml_file_content.encode())
    network.upload_file(config.get_server_config(config.Server.PAYMENT), txt_file_name, txt_file_content.encode())

    return True


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
