# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
from odoo.exceptions import Warning
from . import number_to_letter


class ReportDocCredit(models.AbstractModel):

    _name = "report.jim_doc_credit.doc_credit"

    @api.model
    def render_html(self, docids, data=None):

        name_doc = "jim_doc_credit.doc_credit"
        report_obj = self.env["report"]
        report = report_obj._get_report_from_name(name_doc)
        payment = self.env["account.payment"].browse(docids)

        lines_total_amount = 0.00
        lines_total_qty = 0.00
        lines = []
        symbol = payment.purchase_id.currency_id.symbol

        for line in payment.purchase_id.order_line:
            product_name = line.product_id.with_context(
                partner_id=payment.purchase_id.partner_id.id
            ).name_get()
            product_qty = line.product_qty
            product_uom = line.product_id.uom_id.sga_uom_base_code
            subtotal = line.price_subtotal
            product_price_unit = line.price_unit
            lines_total_amount += subtotal
            lines_total_qty += product_qty

            line_data = {
                "description": product_name[0][1],
                "qty": product_qty,
                "uom": product_uom,
                "price_unit": product_price_unit,
                "subtotal": subtotal,
            }

            lines.append(line_data)

        docargs = {
            "doc_ids": docids,
            "doc_model": report.model,
            "docs": payment,
            "lines": lines,
            "total_amount": lines_total_amount,
            "total_qty": lines_total_qty,
            "symbol": symbol,
            "total_amount_text": number_to_letter.to_word(lines_total_amount),
        }
        return report_obj.render(name_doc, docargs)
