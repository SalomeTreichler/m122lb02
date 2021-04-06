from datetime import datetime, timedelta

import config
import re
import string
import logging
from typing import Callable, Dict, List
from xml.sax import saxutils


def parse_xml(content: bytes):
    """Parse data file to text file

    args:
        content (bytes): Content of the data file

    return:
        Parsed XML file
    """
    data_matrix = _generate_matrix(content)

    _check_matrix(data_matrix)

    # Calculate fields that are not in the data file
    due_date = f"{data_matrix[0][3]} {data_matrix[0][4]}"
    deadline = _calculate_deadline(data_matrix)
    position_count = len(data_matrix[3:])
    price_total = _calculate_price_total(data_matrix)

    ignore_dict = {
        "positions": "$positions",
        "deadline": deadline,
        "position_count": position_count,
        "price_total": price_total
    }

    # Parse the body of the file (Everything except positions)
    body = _parse_file(
        data_matrix, config.get_template("invoice_xml"),
        _invoice_prep, ignore_dict)

    # Parse positions
    positions = ""
    index_id = 1
    for position in data_matrix[3:]:
        if len(position) != 7:
            raise IndexError(f"Position {index_id} has not the correct amount of columns")

        position_parsed = _parse_file([position], config.get_template("invoice_positions_xml"), ignore_dict={
            "position_id": str(index_id),
            "due_date": due_date
        })
        positions += position_parsed
        positions += "\n"
        index_id += 1

    parsed_result = string.Template(body).substitute(
        positions=positions)

    return _get_filename(data_matrix, "xml"), parsed_result


def parse_text(content: bytes) -> (str, str):
    """Parse data file to text file

    args:
        content (bytes): Content of the data file

    return:
        Parsed TXT file
    """
    data_matrix = _generate_matrix(content)

    _check_matrix(data_matrix)

    ignore_dict = {
        "positions": "$positions",
        "deadline": _calculate_deadline(data_matrix)
    }

    # Parse the body of the file (Everything except positions)
    body = _parse_file(
        data_matrix, config.get_template("invoice_txt"),
        _invoice_prep, ignore_dict)

    # Parse positions
    positions = ""
    index_id = 1
    for position in data_matrix[3:]:
        if len(position) != 7:
            raise IndexError(f"Position {index_id} has not the correct amount of columns")

        # Pass 2 dimensional array for correct parsing (Y is always 0 in this case)
        position_parsed = _parse_file([position], config.get_template("invoice_positions_txt"))
        positions += position_parsed
        positions += "\n"
        index_id += 1

    parsed_result = string.Template(body).substitute(positions=positions)

    return _get_filename(data_matrix, "txt"), parsed_result


def _check_matrix(data_matrix: List[List]):
    """Checks if data matrix is valid

    args:
        data_matrix (List[List]): Data matrix to work with

    raises:
        IndexError: Something is wrong
    """
    if len(data_matrix) < 3:
        raise IndexError("Not enough rows to process file")

    if len(data_matrix[0]) != 6:
        raise IndexError("Row 1 has not the right amount of columns")
    if len(data_matrix[1]) != 8:
        raise IndexError("Row 1 has not the right amount of columns")
    if len(data_matrix[2]) != 5:
        raise IndexError("Row 1 has not the right amount of columns")


def _calculate_price_total(data_matrix: List[List]):
    """Calculate price of all positions

    args:
        data_matrix (List[List]): Data matrix to work with

    returns
        (str): Total price of all positions
    """
    price = 0
    for position in data_matrix[3:]:
        price += int(float(position[5]))

    return price


def _calculate_deadline(data_matrix: List[List]):
    """Calculate invoice deadline

    args:
        data_matrix (List[List]): Data matrix to work with

    returns
        (str): Deadline of invoice or "<Invalid>" on failure
    """
    date_format = config.get_date_invoice_format()
    try:
        date = datetime.strptime(data_matrix[0][3], date_format)
        days_to_respond = timedelta(days=int(data_matrix[0][5].split('_')[1]))

        return (date + days_to_respond).strftime(date_format)
    except ValueError:
        logging.error(f"Failed to parse date from invoice: {data_matrix[0][3]} with {date_format}")
        return "<Invalid>"


def _generate_matrix(content):
    """Generates a data matrix for parsing

    This function assumes that the file was not prepared for auto parsing.

    args:
        content (str): The data file content

    returns:
        (List[List]): Data matrix from data file
    """
    return list(
        map(lambda line: line.split(";"), content.decode("utf-8").splitlines()))


def _parse_file(
        data_matrix: List[List], template_file: str,
        prep_autoparse: Callable[[List[List]],None]=lambda a:a,
        ignore_dict: Dict[str, str]={}):
    """Parse a file with the auto-parser

    args:
        data_matrix (List[List]): Data matrix from data file
        template_file: Template file to use for parsing
        prep_autoparse: Auto parse preparation function, if present
        ignore_dict: Dictionary with static replacement parameters

    returns:
        Auto-parse parsed file
    """

    prep_autoparse(data_matrix)
    template = open(template_file).read()

    return _auto_parse(data_matrix, template, ignore_dict)


def _invoice_prep(data_matrix: List[List]):
    """Prepares data matrix to auto parse

    args:
        data_matrix ([][]): Data matrix from data file
    """
    # Rechnung_xxxxx -> xxxxx
    data_matrix[0][0] = data_matrix[0][0].split("_")[1]

    # Auftrag_xxxxx -> xxxxx
    data_matrix[0][1] = data_matrix[0][1].split("_")[1]


def _auto_parse(data_matrix, template, ignore_dict={}):
    """Auto parses data matrix to txt or xml version

    This function replaces all $autoparse_xx placeholders
    with their corresponsing data in the data matrix.

        e.g. $autoparse_23 == data_matrix[2][3]
    
    All tags that are not in the format $autoparse_xx have to be present
    in the ignore dict with a specified static value. Otherwise the program
    will exit.
    
    args:
        data_matrix (List[List]): Data matrix from data file
        template (str): Template string with auto-parse placeholders
        ignore_dict (Dict): Dictionary with static tags that are ignored
                            during auto parsing. This dict should contain
                            ALL tas that are not $autoparse_xx tags.
    
    returns:
        (str): Auto parsed template string
    """
    # Get all placeholders
    placeholders = re.findall(r"\$autoparse_\d{2}", template)

    placelement_map = {}
    placelement_map.update(ignore_dict)

    for placeholder in placeholders:
        pos_x = int(re.findall(r"\d", placeholder)[0])
        pos_y = int(re.findall(r"\d", placeholder)[1])
        try:
            placelement_map[placeholder[1:]] = saxutils.escape(data_matrix[pos_x][pos_y])
        except IndexError as _:
            logging.fatal(f"Invalid auto-parse placeholder: {placeholder}")
            exit(1)
    
    try:
        return string.Template(template).substitute(placelement_map)
    except KeyError as e:
        logging.fatal(f"Invalid auto-parse placeholder: {e}")
        exit(1)


def _get_filename(data_matrix: List[List], file_ext: str):
    """Get file name for a invoice file

    args:
        data_matrix (List[List]): Data matrix from data file
        file_ext (str): Extension of the file

    returns:
        (str): Generated name of the invoice file
    """
    invoice_nr = data_matrix[0][0]
    customer_nr = data_matrix[1][1]

    return f"{customer_nr}_{invoice_nr}_invoice.{file_ext}"


def get_email_receiver(invoice_content: bytes):
    """Get email receiver name and address from invoice data file"""
    data_matrix = _generate_matrix(invoice_content)

    return data_matrix[1][3], data_matrix[1][7]