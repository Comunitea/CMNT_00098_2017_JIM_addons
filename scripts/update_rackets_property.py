#!/usr/bin/env python
# -*- coding: utf-8 -*-

session.open(db='odoo_12_DISMAC_14_02')


domain = [('is_company', '=', True),('customer', '=', True)]
domain= [('id', '=', 123833)]
partners_racket = session.env['res.partner'].with_context(force_company=26).search(domain)

print(len(partners_racket))
count = 0
for partner in partners_racket:
    print(partner.name)
    vals = {}
    if not partner.customer_payment_mode_id:
        vals['customer_payment_mode_id'] = 224
        #partner.write({'customer_payment_mode_id': 224})
    if not partner.property_account_position_id:
        fp_JIM_id = partner.sudo().with_context(force_company=1).property_account_position_id
        print("FP en JIM")
        print(fp_JIM_id)
        if fp_JIM_id:
            fp_name =  fp_JIM_id.name
            print(fp_name)
            fp = session.env['account.fiscal.position'].search([('name', '=', fp_name)], limit=1) 
            if fp:
                fp_id = fp.id
            else:
                fp_id = False
        else:
            fp_id = False
        if fp_id:
            vals['property_account_position_id'] = fp_id
        #partner.write({'property_account_position_id': fp_id})
    if not partner.property_payment_term_id:
        vals['property_payment_term_id'] = 28
        #partner.write({'property_payment_term_id': 28})
    if vals:
        print(vals)
        partner.with_context(b2b_evaluate=False).write(vals)
    count += 1
    print(count)
    print("--------")

session.cr.commit()
exit()