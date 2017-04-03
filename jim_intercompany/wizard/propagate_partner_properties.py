# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import models, api


class PropagatePartnerProperties(models.TransientModel):
    _name = 'propagate.partner.properties'

    @api.multi
    def do_propagate(self):
        t_partner = self.env['res.partner']

        partner_ids = self._context.get('active_ids', [])
        partner_objs = t_partner.browse(partner_ids)
        current_company = self.env['res.users'].browse(self._uid).company_id.id

        domain = [('id', '!=', current_company)]
        company_objs = self.env['res.company'].sudo().search(domain)
        fields_list = [
            'property_payment_term_id',
            'property_supplier_payment_term_id',
        ]

        company_fields_list = [
            'property_account_payable_id',
            'property_account_receivable_id',
            'property_account_position_id',
            'property_product_pricelist'
        ]
        for partner in partner_objs:
            for company in company_objs:
                # property_payment_term_id
                ctx = {'force_company': company.id}
                partner2 = t_partner.with_context(ctx).browse(partner.id)
                eval_dic = {'partner': partner}

                # SHARED objects between companies
                for field in fields_list:
                    field_eval = 'partner.' + field
                    model_value = eval(field_eval, eval_dic)
                    if model_value:
                        # vals[field] = model_value.id
                        partner2.sudo().write({field: model_value.id})

                # NON SHARED objects between companies
                for field in company_fields_list:
                    field_eval = 'partner.' + field
                    model_value = eval(field_eval, eval_dic)
                    model_name = model_value._name
                    if model_value:
                        # Search equivalent in other company
                        domain = [
                            ('company_id', '=', company.id),
                            ('name', '=', model_value.name)
                        ]
                        model_obj = self.env[model_name].sudo().search(domain,
                                                                       limit=1)
                        if model_obj:
                            # vals[field] = model_obj.id
                            partner2.sudo().write({field: model_obj.id})
