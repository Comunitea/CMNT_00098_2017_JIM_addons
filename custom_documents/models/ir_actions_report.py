# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models,api, fields
import base64
import os
import logging
import tempfile
from contextlib import closing
from pyPdf import PdfFileWriter, PdfFileReader

_logger = logging.getLogger(__name__)

class ReportCompanyAdvise(models.Model):

    _name = 'report.company.advise'

    @api.multi
    def compute_complete_name(self):
        for rca in self:
            rca.complete_name = '{}.{}'.format(rca.model_id, rca.name)


    complete_name = fields.Char(compute="compute_complete_name")
    name = fields.Char(related='xml_id.name', string='Nombre')
    xml_id = fields.Many2one('ir.model.data')
    model_id = fields.Char(related='xml_id.module', string='Modelo')
    active = fields.Boolean('Activo', default=True)
    res_id = fields.Integer(related='xml_id.res_id')


    #
    # name = fields.Char(string='External Identifier', required=True,
    #                    help="External Key/Identifier that can be used for "
    #                         "data integration with third-party systems")
    # complete_name = fields.Char(compute='_compute_complete_name', string='Complete ID')
    # model = fields.Char(string='Model Name', required=True)
    # module = fields.Char(default='', required=True)
    # res_id = fields.Integer(string='Record ID', help="ID of the target record in the database")
    # noupdate = fields.Boolean(string='Non Updatable', default=False)
    # date_update = fields.Datetime(string='Update Date', default=fields.Datetime.now)
    # date_init = fields.Datetime(string='Init Date', default=fields.Datetime.now)
    # reference = fields.Char(string='Reference', compute='_compute_reference', readonly=True, store=False)


class ClassReport(models.Model):
    _inherit ="report"

    @api.model
    def get_pdf(self, res_ids, report_name, html=None, data=None):

        IrActionsReport = self._get_report_from_name(report_name)
        model = IrActionsReport.model
        model_ids = self.env[model].browse(res_ids)

        if IrActionsReport.xml_id in self.env['report.company.advise'].search([]).mapped('complete_name'):
            pdfdatas = []
            temporary_files = []
            advise_pdf = {}
            for model_id in model_ids:
                model_pdf = super(ClassReport, self).get_pdf([model_id.id], report_name=report_name, html=html, data=data)
                pdfdatas.append(model_pdf)
                if model_id.company_id.show_company_advise:
                    if not model_id.company_id.name in advise_pdf.keys():
                        advise_pdf[model_id.company_id.name] = super(ClassReport, self).get_pdf([model_id.company_id.id], report_name='custom_documents.company_advise')
                    pdfdatas.append(advise_pdf[model_id.company_id.name])
            if pdfdatas:
                pdfdocuments = []
                for pdfcontent in pdfdatas:
                    pdfreport_fd, pdfreport_path = tempfile.\
                        mkstemp(suffix='.pdf', prefix='report.tmp.')
                    temporary_files.append(pdfreport_path)
                    with closing(os.fdopen(pdfreport_fd, 'wb')) as pdfr:
                        pdfr.write(pdfcontent)
                    pdfdocuments.append(pdfreport_path)
                entire_report_path = self._merge_pdf(pdfdocuments)
                temporary_files.append(entire_report_path)
                with open(entire_report_path, 'rb') as pdfdocument:
                    content = pdfdocument.read()
                # Manual cleanup of the temporary files
                for temporary_file in temporary_files:
                    try:
                        os.unlink(temporary_file)
                    except (OSError, IOError):
                        _logger.error('Error when trying to remove '
                                      'file %s' % temporary_file)
                return content

        return super(ClassReport, self).get_pdf(res_ids, report_name=report_name, html=html, data=data)



