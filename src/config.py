import enum
import json
import logging
from typing import Optional

from pydantic import BaseModel


class Server(enum.Enum):
    CUSTOMER = 1
    PAYMENT = 2
    EMAIL = 3


_SERVER_CONFIG_PATHS = {
    Server.CUSTOMER: "./data/server_customer.json",
    Server.PAYMENT: "./data/server_payment.json",
    Server.EMAIL: "./data/server_email.json"
}

_GENERAL_CONFIG = "./data/config.json"


class ServerConfig(BaseModel):
    hostname: str
    username: str
    password: str
    files_in: Optional[str]
    files_out: Optional[str]


def get_server_config(server):
    return _load_server_config(_SERVER_CONFIG_PATHS[server])


def __getattr__(name):
    return get()[name]


def get_mail_template():
    return get()["email_template"]


def get_mail_receiver_name():
    return get()["email_receiver_name"]


def get_mail_sender_name():
    return get()["email_sender_name"]


def get_mail_message():
    return get()["email_message"]


def get_mail_sender():
    return get()["email_sender"]


def get_mail_receiver():
    return get()["email_receiver"]


def get_cache_folder():
    return get()["cache_folder"]


def get_invoice_pattern():
    return get()["patterns"]["invoice"]


def get_receipt_pattern():
    return get()["patterns"]["receipt"]


def get_template(name: str):
    return get()[f"template_{name}"]


def get_date_file_format():
    return get()["formats"]["date_file"]


def get_date_email_format():
    return get()["formats"]["date_email"]


def get_time_file_format():
    return get()["formats"]["time_file"]


def get_time_email_format():
    return get()["formats"]["time_email"]


def get_date_invoice_format():
    return get()["formats"]["date_invoice"]


def get_email_sender():
    return get()["email_sender"]


def get_email_sender_name():
    return get()["email_sender_name"]


def get():
    try:
        return json.loads(open(_GENERAL_CONFIG).read())
    except IOError as e:
        logging.fatal(f"Failed to open general config file {_GENERAL_CONFIG}")
        exit(1)
    except json.decoder.JSONDecodeError as e:
        logging.fatal(f"Failed to decode general config file: {e}")
        exit(1)


def _load_server_config(path):
    try:
        return ServerConfig(**json.loads(open(path).read()))
    except IOError as _:
        logging.fatal(f"Failed to open general config file {_GENERAL_CONFIG}")
        exit(1)
    except (TypeError, json.decoder.JSONDecodeError) as e:
        logging.fatal(f"Failed to decode server config file: {e}")
        exit(1)