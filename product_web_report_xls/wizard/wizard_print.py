# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from odoo import fields, api, models


class PrintWizard(models.TransientModel):
    _name = 'wzd.product.report'


    @api.multi
    def _default_report_id(self):
        return self.env.context.get('active_id', False)

    @api.multi
    def _default_report_xml_id(self):
        report = self.env['product.product'].browse(
            self._default_report_id())
        return report.template_id.report_xml_id.id

    report_id = fields.Many2one('wzd.product.report', "Report",
                                default=_default_report_id)
    report_xml_id = fields.Many2one('ir.actions.report.xml', "Design",
                                    default=_default_report_xml_id)

    @api.multi
    def print_report(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': self.report_xml_id.report_name,
            'datas': {
                'ids': self.report_id.ids,
            }
        }

    def xls_export(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids[0], context=context)
        datas = {
            'report_id': (data.get('report_id') and
                          data['report_id'][0] or None),
            'report_name': (data.get('report_id') and
                            data['report_id'][1] or None),
            'report_design': (data.get('report_xml_id') and
                              data['report_xml_id'][1] or None),
            'ids': context.get('active_ids', []),
            'model': 'account.balance.reporting',
            'form': data,
        }
        rpt_facade = self.pool['ir.actions.report.xml']
        report_xml = None
        if data.get('report_xml_id'):
            report_xml_id = data['report_xml_id']
            report_xml_ids = rpt_facade.search(
                cr, uid, [('id', '=', report_xml_id[0])], context=context)
            report_xml_id = report_xml_ids and report_xml_ids[0] or None
            if report_xml_id:
                report_xml = rpt_facade.browse(
                    cr, uid, [report_xml_id], context=context)[0]
            if report_xml:
                return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'reporting.xls',
                    'datas': datas,
                }
        return True
