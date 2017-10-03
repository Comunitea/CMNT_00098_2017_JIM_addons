# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _
from odoo.exceptions import UserError

import odoo.addons.decimal_precision as dp

class StockQuant(models.Model):

    _inherit = "stock.quant"

    def soluciona(self):
        self._cr.execute(
            """SELECT DISTINCT(SQ.id) FROM stock_move SM 
            INNER JOIN stock_quant_move_rel SQM ON SM.id=SQM.move_id
            INNER JOIN stock_quant SQ ON SQ.id=SQM.quant_id
            WHERE SQ.company_id != SM.company_id""")

        problem_quant_ids = [r[0] for r in self._cr.fetchall()]
        n_quants = len(problem_quant_ids)
        processed = 0
        print n_quants
        for quant in self.browse(problem_quant_ids):
            print "Procesando " + str(quant.id)
            moves_sc = quant.history_ids.filtered(
                lambda c: quant.company_id == c.company_id)\
                .sorted(key=lambda r: r.create_date)
            moves_dc = quant.history_ids.filtered(
                lambda c: quant.company_id != c.company_id) \
                .sorted(key=lambda r: r.create_date)
            # Copiamos quant inverso en ubicacion de origen
            new_quant_sc = quant.copy(
                {'location_id': moves_sc[0].location_id.id,
                 'qty': -quant.qty})
            #lo asignamos al movimiento original
            moves_sc[0].write({'quant_ids':[(4, new_quant_sc.id)]})

            new_quant_dc = new_quant_sc.copy(
                {'company_id': moves_dc[0].company_id.id,
                 'qty': -new_quant_sc.qty})

            # Escribe nuevo queant en la compañía
            moves_dc.write(({'quant_ids': [(4, new_quant_dc.id)]}))

            #Quieta los quants de la otra compañía
            moves_dc.write(({'quant_ids': [(3, quant.id)]}))
            processed += 1
            print "Procesados " + str(processed) + " de " + str(n_quants)



