import logging
import os
import shutil
import zipfile
from typing import List

import config

_CACHE_FOLDER = config.get_cache_folder()


def _get_cache_filename(filename: str):
    """Get path of a file in cache by file name

    args:
        filename (str): Name of the file (relative)

    returns:
        (str): Name of the file (absolute to cwd)
    """
    return f"{_CACHE_FOLDER}/{filename}"


def write(filename: str, content: str) -> None:
    """Write a cache file

    args:
        filename: Name of the file to write
        content: Content to write
    """
    open(_get_cache_filename(filename), mode='w').write(content)


def read(filename: str) -> str:
    """Read a cache file as string

    args:
        filename: Name of the file to read
    """
    return open(_get_cache_filename(filename), mode='r').read()


def read_binary(filename: str) -> bytes:
    """Read a cache file as bytes

    args:
        filename: Name of the file to read
    """
    return open(_get_cache_filename(filename), mode='rb').read()


def get_invoice_numbers() -> List[str]:
    """Get the numbers of all invoices in cache

    returns:
        List of numbers of all invoices in cache
    """
    file_list = list(
        map(
            lambda filename: filename.split('_')[1],
            list(
                filter(
                    lambda filename: "invoice" in filename, os.listdir(_CACHE_FOLDER))
            )
        )
    )
    if not file_list:
        logging.info("No cached invoices found. Exiting")
        exit(0)
    return file_list


def get_invoice_by_number(invoice_number: str) -> str or None:
    """Get an invoice from cache by invoice number

    args:
        invoice_number (str): Number of the invoice

    returns:
        (str or None): Invoie file name or None when invoice was not found
    """
    file_list = list(filter(
        lambda filename: invoice_number in filename and "invoice.txt" in filename, os.listdir(_CACHE_FOLDER)))
    if len(file_list) < 1:
        logging.error(f"No cached invoice found with number '{invoice_number}'")
        return None
    elif len(file_list) > 1:
        logging.error(f"More than one invoice cached with number '{invoice_number}'")
        return None
    return file_list[0]


def zip_files(invoice_file_name: str, receipt_file_name: str, zip_file_name: str):
    """Create a ZIP archive with invoice and receipt

    args:
        invoice_file_name (str): File name of the invoice
        receipt_file_name (str): File name of the receipt
        zip_file_name (str): File name of the Zip
    """
    # Create temporary files
    shutil.copy(_get_cache_filename(invoice_file_name), invoice_file_name)
    shutil.copy(_get_cache_filename(receipt_file_name), receipt_file_name)
    with zipfile.ZipFile(_get_cache_filename(zip_file_name), 'w') as zip:
        zip.write(invoice_file_name)
        zip.write(receipt_file_name)

    # Remove temporary files
    os.remove(invoice_file_name)
    os.remove(receipt_file_name)


def clear(invoice_number: str):
    """Removes all cached files related to an invoice

    args:
        invoice_number (str): Invoice number
    """
    for file in os.listdir(_CACHE_FOLDER):
        if invoice_number in file:
            os.remove(_get_cache_filename(file))