# -*- coding: utf-8 -*-
from .pd_base import BaseExtClass
from .. import tools


class SaleOrder(BaseExtClass):
    _inherit = "sale.order"

    fields_to_watch = ('id', 'partner_id', 'name', 'date_order', 'amount_total', 'template_lines', 'price_unit',
                       'state')

    def is_notifiable(self):
        return self.state == "pending" \
           and self.company_id.id == 1 \
           and self.partner_id.is_notifiable()

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

        self.xml = podocuments.format(
            "17#" + str(self.id),                       # IdDocs
            self.partner_id.ref or self.partner_id.id,  # CardCode
            "17",                                       # ObjType
            self.id,                                    # DocEntry
            self.name,                                  # DocNum
            tools.format_date(self.date_order),         # DocDate
            self.amount_total                           # DocTotal
        )

        self.obj_type = 'DOCUMENTS'
