# -*- coding: utf-8 -*-
from datetime import datetime


def format_date(date_string=None,
                input_date_format='%Y-%m-%d %H:%M:%S',
                output_date_format='%Y%m%d'):

    if not date_string:
        date_string = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return datetime.strptime(date_string, input_date_format).strftime(output_date_format)
