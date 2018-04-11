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

    def _get_report_columns(self, report, stock_field, valued):
        #type
        # default = strign
        # int, float, boolean
        columns = {
            0: {'header': _('Name'), 'field': 'display_name', 'width': 80},
            1: {'header': _('Code'), 'field': 'default_code', 'width': 20},
            2: {'header': _('Tags'), 'field': 'tag_names', 'width': 50},
            3: {'header': _('Web'), 'field': 'web', 'width': 10, 'type': 'boolean'},
            4: {'header': _('Stock'), 'field': stock_field, 'width': 15, 'type': 'float'},
        }
        if valued:
            columns[5] = {'header': _('cantidad_total'), 'field': 'cantidad_total', 'width': 15, 'type': 'float'}
            columns[6] = {'header': _('importe_total'), 'field': 'importe_total', 'width': 15, 'type': 'float'}
            columns[7] = {'header': _('arancel'), 'field': 'arancel', 'width': 15, 'type': 'float'}
            columns[8] = {'header': _('Precio Medio'), 'field':
                'precio_unitario', 'width': 15, 'type': 'float'}
            columns[9] = {'header': _('porcentaje_arancel'), 'field': 'porcentaje_arancel', 'width': 15, 'type': 'float'}
            columns[10] = {'header': _('delivery'), 'field': 'delivery', 'width': 15, 'type': 'float'}
           #columns[11] = {'header': _('Media precio unit.'), 'field':
           #    'price_unit',
           #               'width': 15, 'type': 'float'}
            columns[11] = {'header': _('Precio coste medio SAP'), 'field':
                'standard_price', 'width': 15, 'type': 'float'}
            columns[12] = {'header': _('Numero lineas'), 'field': 'num_lineas',
                           'width': 10, 'type': 'float'}
        return columns

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
