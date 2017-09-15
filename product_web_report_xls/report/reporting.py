# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

import time
from odoo.report import report_sxw
from odoo.tools.translate import translate

_ir_translation_name = 'product.product.reporting.print'

class ProductProductReportingPrint(report_sxw.rml_parse):

    def set_context(self, objects, data, ids, report_type=None):
        super(ProductProductReportingPrint, self).set_context(
            objects, data, ids)
        self.report_type = report_type
        self.report_id = data['report_id']
        self.report_name = data['report_name']
        self.report_design = data['report_design']
        self.localcontext.update({
            'additional_data': self._get_additional_data(),
        })

    def __init__(self):
        super(ProductProductReportingPrint, self).__init__()
        self.localcontext.update({
            'time': time,
            'lines': self._lines,
            '_': self._,
        })
        self.context = self._context

    def _(self, src):
        lang = self._context.get('lang', 'en_US')
        return translate(self.cr, _ir_translation_name, 'report', lang,
                         src) or src

    def _get_additional_data(self):
        abr_obj = self.env['product.product']
        abr = abr_obj.browse()
        fields = {}
        return fields

    def _lines(self, obj):
        user = self.env.uid
        ctx_lang = {'lang': user.lang}
        non_zero = self.report_design
        # No SQL is used, as performance should not be a problem using
        # already calculated values.
        lines = []
        for line in obj.line_ids:
            line_fields = {
                'display_name': line.display_name,
                'default_code': line.default_code,
                'tag_names': line.tag_names,
                'web': line.web,
                'global_real_stock': line.global_real_stock
            }
            lines.append(line_fields)
        return lines


report_sxw.report_sxw(
    'report.product.product.web.reporting.print', 'product.product.product',
    parser=ProductProductReportingPrint, header=False)
