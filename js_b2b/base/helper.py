# -*- coding: utf-8 -*-
from datetime import datetime

class MsgTypes:

    HEADER = '\033[95m'
    INFO = '\033[94m'
    WARNING = '\033[93m'
    OK = '\033[92m'
    ERROR = '\033[91m'
    UNDERLINE = '\033[4m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

class OutputHelper:

    DIVIDER = "=" * 80

    @staticmethod
    def print_text(msg, msg_type=MsgTypes.INFO, include_timestamp=True):
        print("\n")
        print("{}{}{}".format(msg_type, OutputHelper.DIVIDER, MsgTypes.ENDC))

        if include_timestamp:
            print("{}{}{}".format(msg_type, datetime.now(), MsgTypes.ENDC))

        print("    {}{}{}".format(msg_type, msg, MsgTypes.ENDC))
        print("{}{}{}".format(msg_type, OutputHelper.DIVIDER, MsgTypes.ENDC))
        print("\n")

    @staticmethod
    def format_date(date_string=None, input_date_format='%Y-%m-%d %H:%M:%S', output_date_format='%Y%m%d'):
        if not date_string:
            date_string = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return datetime.strptime(date_string, input_date_format).strftime(output_date_format)
