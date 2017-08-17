# -*- coding: utf-8 -*-
from datetime import datetime


class MsgTypes:
    def __init__(self):
        pass

    # HEADER = '\033[95m'

    INFO = '\033[94m'
    OK = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'

    ENDC = '\033[0m'
    # BOLD = '\033[1m'
    # UNDERLINE = '\033[4m'


class OutputHelper:
    def __init__(self): pass

    @staticmethod
    def print_text(msg, msg_type=MsgTypes.INFO, include_timestamp=True):

        print("\n")
        print("{}{}{}".format(msg_type, "=" * 80, MsgTypes.ENDC))
        if include_timestamp:
            print("{}{}{}".format(msg_type, datetime.now(), MsgTypes.ENDC))
        print("\t{}{}{}".format(msg_type, msg, MsgTypes.ENDC))
        print("{}{}{}".format(msg_type, "=" * 80, MsgTypes.ENDC))
        print("\n")

    @staticmethod
    def debug(msg, include_timestamp=True):
        print("\n")
        print("{}{}{}".format(MsgTypes.ERROR, "=" * 80, MsgTypes.ENDC))
        if include_timestamp:
            print("{}{}{}".format(MsgTypes.INFO, datetime.now(), MsgTypes.ENDC))
        print("\t{}{}{}".format(MsgTypes.WARNING, msg, MsgTypes.ENDC))
        print("{}{}{}".format(MsgTypes.ERROR, "=" * 80, MsgTypes.ENDC))
        print("\n")
