# -*- coding: utf-8 -*-
from .pd_base import BaseExtClass
from .. import tools


class AccountInvoice(BaseExtClass):
    _inherit = "account.invoice"

    fields_to_watch = ('id', 'commercial_partner_id', 'name', 'date_invoice', 'amount_total', 'state')

    def is_notifiable(self):
        return self.state == "open" \
           # and self.company_id.id == 1 \
           and (self.type == 'out_invoice' or self.type == 'out_refund') \
           and self.number \
           and self.commercial_partner_id.is_notifiable()

    def set_props(self, unlink=False):
        podocuments = """
                <podocuments>
                  <IdDocs>{}</IdDocs>
                  <CardCode>{}</CardCode>
                  <ObjType>{}</ObjType>
                  <DocEntry>{}</DocEntry>
                  <DocNum>{}</DocNum>
                  <DocDate>{}</DocDate>
                  <DocTotal>{}</DocTotal>
                </podocuments>
              """

        # factura = 13; factura rectificativa = 14
        objtype = '13' if self.type == 'out_invoice' else '14'

        self.xml = podocuments.format(
            objtype + "#O#" + str(self.id),             # IdDocs
            self.commercial_partner_id.ref or self.commercial_partner_id.id,  # CardCode
            objtype,                                    # ObjType
            self.id,                                    # DocEntry
            self.number,                                # DocNum
            tools.format_date(self.date_invoice, '%Y-%m-%d'),  # DocDate
            self.amount_total                           # DocTotal
        )

        self.obj_type = 'DOCUMENTS'
