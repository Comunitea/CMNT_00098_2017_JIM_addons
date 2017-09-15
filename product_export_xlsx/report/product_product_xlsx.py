# -*- coding: utf-8 -*-



from . import abstract_report_xlsx
from odoo.report import report_sxw
from odoo import _


class ProductWebXslx(abstract_report_xlsx.AbstractReportXslx):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):

        super(ProductWebXslx, self).__init__(
            name, table, rml, parser, header, store)

    def _get_report_name(self):
        return _('Product web')

    def _get_report_columns(self, report):
        #type
        # default = strign
        # int, float, boolean
        return {
            0: {'header': _('Name'), 'field': 'display_name', 'width': 80},
            1: {'header': _('Code'), 'field': 'default_code', 'width': 20},
            2: {'header': _('Tags'), 'field': 'tag_names', 'width': 50},
            3: {'header': _('Web'), 'field': 'web', 'width': 10, 'type': 'boolean'},
            4: {'header': _('Stock'), 'field': 'web_global_stock', 'width': 15, 'type': 'float'},
        }

    def _get_report_filters(self, report):
        return []

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 2

    def _get_col_pos_initial_balance_label(self):
        return 5

    def _get_col_count_final_balance_name(self):
        return 5

    def _get_col_pos_final_balance_label(self):
        return 5

    def _generate_report_content(self, workbook, report):

        for product in report:
            self.write_line(product)
            # Write account title

    def write_ending_balance(self, my_object, type_object):
        """Specific function to write ending balance for General Ledger"""
        if type_object == 'partner':
            name = my_object.name
            label = _('Partner ending balance')
        elif type_object == 'account':
            name = my_object.code + ' - ' + my_object.name
            label = _('Ending balance')
        super(ProductWebXslx, self).write_ending_balance(
            my_object, '', ''
        )


ProductWebXslx(
    'report.product_web_xls',
    'product.product',
    parser=report_sxw.rml_parse
)
