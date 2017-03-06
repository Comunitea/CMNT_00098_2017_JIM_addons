# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _, exceptions
import os
import codecs
import re
from datetime import datetime
from odoo.modules.registry import RegistryManager
import logging
_logger = logging.getLogger(__name__)

SerialMap = {'C': 'Canarias', 'D': 'Transporte', 'G': 'Inmovilizado',
             'J': 'Gastos financieros', 'M': 'Patrocinios',
             'AXM': 'La Caixa', 'F': 'Obras', 'H': 'Software',
             'AL': 'Alquileres', 'RC': 'Canarias', 'RD': 'Transporte',
             'RG': 'Inmovilizado', 'RJ': 'Gastos financieros',
             'RM': 'Patrocinios', 'DXM': 'La Caixa', 'RF': 'Obras',
             'RH': 'Software', 'RAL': 'Alquileres'}


class A3ImportLog(models.Model):

    _name = "a3.import.log"

    name = fields.Char("Filename", required=True)
    state = fields.Selection(
        (('new', 'New'), ('imported', 'Imported'), ('error', 'Error')),
        default='new')
    errors = fields.Text()

    @api.multi
    def move_imported_files(self, importation_folder, process_folder):
        for doc in self:
            if doc.state == 'imported':
                from_file = '%s%s%s' % (importation_folder, os.sep, doc.name)
                to_file = '%s%s%s' % (process_folder, os.sep, doc.name)
                os.rename(from_file, to_file)

    @api.model
    def import_invoice(self, line, company, refund=False):
        invoice_number = line[58:68].strip()
        letters = re.findall('\d*\D+', invoice_number)
        tag_ids = []
        if letters and letters[0] in SerialMap:
            tags = self.env["account.invoice.tag"].\
                search([('name', '=', SerialMap[letters[0]])])
            if tags:
                tag_ids.append(tags[0].id)
        invoice_vals = {
            'type': refund and 'out_refund' or 'out_invoice',
            'journal_id': self.env["account.journal"].
            search([('type', '=', 'sale'),
                    ('company_id', '=', company.id)])[0].id,
            'currency_id': company.currency_id.id,
            'number': invoice_number,
            'invoice_number': invoice_number,
            'date_invoice': datetime.
            strftime(datetime.strptime(line[6:14], "%Y%m%d"), "%Y-%m-%d"),
            'company_id': company.id,
            'tag_ids': [(6, 0, tag_ids)]
        }
        return invoice_vals

    @api.model
    def import_invoice_line(self, line, company):
        taxes = self.env["account.tax"]
        national_valid_codes = ['S_IVA21B', 'S_IVA4B', 'S_IVA0', 'S_IVA10B']
        intracomunity_valid_codes = ['S_IVA0_IC']
        extracomunity_valid_codes = ['S_IVA0_E']
        recharge_valid_code = ['S_REQ05', 'S_REQ014', 'S_REQ52']
        fiscal_position_code = line[99:101]
        tax_domain = [('type_tax_use', '=', 'sale'),
                      ('company_id', '=', company.id)]

        iva_tax = float(line[115:120])
        iva_domain = [('amount', '=', iva_tax)]
        iva_domain.extend(tax_domain)
        if fiscal_position_code == "01":
            iva_domain.append(('description', 'in', national_valid_codes))
        elif fiscal_position_code == "03":
            iva_domain.append(('description', 'in',
                               intracomunity_valid_codes))
        elif fiscal_position_code == "05":
            iva_domain.append(('description', 'in',
                               extracomunity_valid_codes))
        else:
            raise exceptions.\
                UserError(_("Fiscal position code %s has not a parser") %
                          fiscal_position_code)
        iva = self.env["account.tax"].search(iva_domain)
        if iva:
            taxes += iva[0]

        re_tax = float(line[134:139])
        if re_tax:
            re_domain = [('amount', '=', re_tax),
                         ('description', 'in', recharge_valid_code)]
            re_domain.extend(tax_domain)
            re = self.env["account.tax"].search(re_domain)
            if re:
                taxes += re[0]
        irpf_tax = float(line[153:158])
        if irpf_tax:
            irpf_domain = [('amount', '=', irpf_tax),
                           ('description', 'like', '%IRPF%')]
            irpf_domain.extend(tax_domain)
            irpf = self.env["account.tax"].search(irpf_domain)
            if irpf:
                taxes += irpf[0]
        invoice_line_vals = {
            'account_id': self.env["account.account"].
            search([('code', '=', line[15:25]),
                    ('company_id', '=', company.id)])[0].id,
            'name': line[27:57].strip(),
            'price_unit': float(line[101:115]),
            'invoice_line_tax_ids': [(6, 0, taxes.ids)]
        }
        return invoice_line_vals

    @api.model
    def import_partner(self, line, company):
        partner_ref = "C" + line[20:25]
        partner = self.env["res.partner"].\
            with_context(company_id=company.id).\
            search([('ref', '=', partner_ref)])
        if not partner:
            partner_vals = {
                'ref': partner_ref,
                'customer': True,
                'is_company': True,
                'name': line[27:57].strip(),
                'street': line[93:133].strip(),
                'city': line[134:154].strip(),
                'zip': line[154:159].strip(),
                'phone': line[177:187].strip(),
                'to_review': True
            }
            partner = self.env["res.partner"].create(partner_vals)
            vat = line[77:91].strip()
            if vat:
                try:
                    country = self.env["res.country"].\
                        search([('code', '=', vat[:2])])
                    if not country:
                        vat = 'ES' + vat
                    partner.vat = vat
                except:
                    _logger.error(_('VAT %s not valid') % vat)
                finally:
                    partner.comment = vat
            return partner
        else:
            return partner[0]

    @api.multi
    def import_data(self, f):
        with_error = False
        with api.Environment.manage():
            with RegistryManager.get(self.env.cr.dbname).cursor() as new_cr:
                new_env = api.Environment(new_cr, self.env.uid,
                                          self.env.context)
                #Se hace browse con un env diferente para guardar cambios
                doc_ = self.with_env(new_env).browse(self.id)
                try:
                    invoice_vals = {}
                    invoice_line_vals = {}
                    partner = False
                    for line in f.readlines():
                        line_type = line[14]
                        company_code = line[:6]
                        company = self.sudo().env["res.company"].\
                            search([('a3_company_code', '=', company_code)])
                        if line_type == "1":  # factura de venta
                            invoice_vals = doc_.import_invoice(line, company)
                        elif line_type == "2":  # factura rectificativa venta
                            invoice_vals = doc_.\
                                import_invoice(line, company, True)
                        elif line_type == "9":  # detalle de factura
                            invoice_line_vals = doc_.\
                                import_invoice_line(line, company)
                        elif line_type == "C":
                            partner = doc_.import_partner(line, company)
                        else:
                            raise exceptions.\
                                UserError(_("Line type %s has not a parser") %
                                          line_type)
                        if partner:
                            invoice_vals['partner_id'] = partner.id
                            invoice_vals['account_id'] = \
                                partner.property_account_receivable_id.id
                            invoice_vals['fiscal_position_id'] = \
                                partner.property_account_position_id.id
                            invoice_vals['payment_mode_id'] = \
                                partner.customer_payment_mode_id.id
                            invoice_vals['user_id'] = partner.user_id.id
                            invoice = self.with_env(new_env).\
                                env["account.invoice"].create(invoice_vals)
                            invoice_line_vals['invoice_id'] = invoice.id
                            self.with_env(new_env).\
                                env["account.invoice.line"].\
                                create(invoice_line_vals)
                            invoice.compute_taxes()
                            invoice.action_invoice_open()
                            invoice_vals = {}
                            invoice_line_vals = {}
                            partner = False
                except Exception as e:
                    self.errors = '\n%s' % str(e)
                    self.state = 'error'
                    new_env.cr.rollback()
                    with_error = True
                if not with_error:
                    self.state = 'imported'
                    new_env.cr.commit()

    @api.model
    def import_files(self):
        folder = self.env["ir.config_parameter"].\
            search([('key', '=', 'a3.import.path')])
        if not folder:
            _logger.error(_('Not found config parameter a3.import.path'))
            return
        importation_folder = '%s%slecturas' % (folder.value, os.sep)
        process_folder = '%s%sprocesados' % (folder.value, os.sep)
        import_files = [x for x in os.listdir(importation_folder)
                        if x.endswith('.dat')]
        docs = self.env["a3.import.log"]
        for import_file in import_files:
            doc = self.search(
                [('name', '=', import_file),
                 ('state', 'in', ('new', 'error'))])
            if not doc:
                doc_vals = {
                    'name': import_file,
                    'state': 'new',
                }
                doc = self.create(doc_vals)
            docs += doc
            with codecs.open(
                    '%s%s%s' % (importation_folder, os.sep, import_file),
                    'r', 'iso-8859-1') as f:
                doc.import_data(f)
        docs.move_imported_files(importation_folder, process_folder)
