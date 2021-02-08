# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import models, api


class PropagateProductProperties(models.TransientModel):
    _name = 'propagate.product.properties'

    @api.multi
    def do_propagate(self):
        """
        No property fields propaged, only taxes.
        """
        t_product = self.env['product.template']

        product_ids = self._context.get('active_ids', [])
        product_objs = t_product.browse(product_ids)
        current_company = self.env['res.users'].browse(self._uid).company_id.id

        domain = [('id', '!=', current_company)]
        company_objs = self.env['res.company'].sudo().search(domain)
        tax_fields = [
            'taxes_id',
            'supplier_taxes_id',
        ]
        for product in product_objs:
            for field in tax_fields:
                eval_dic = {'product': product}
                field_eval = 'product.' + field
                tax_records = eval(field_eval, eval_dic)
                new_tax_ids = list(tax_records._ids)
                for company in company_objs:
                    ctx = {'force_company': company.id}
                    product2 = t_product.with_context(ctx).browse(product.id)

                    if tax_records:
                        domain = [
                            ('name', 'in', tax_records.mapped('name')),
                            ('company_id', '=', company.id)
                        ]
                        tax_objs = self.env['account.tax'].sudo().\
                            search(domain)
                        if tax_objs:
                            new_tax_ids.extend(list(tax_objs._ids))
                vals = {
                    field: [(6, 0, new_tax_ids)]
                }
                product2.sudo().with_context(b2b_evaluate=False).write(vals)
