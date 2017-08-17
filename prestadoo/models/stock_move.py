# -*- coding: utf-8 -*-
from .pd_base import BaseExtClass
from .. import tools


class StockMove(BaseExtClass):
    _inherit = "stock.move"

    fields_to_watch = ('order_id', 'id', 'product_id', 'product_qty', 'qty_received', 'date_expected', 'state')

    def is_notifiable(self):
        return (self.state == "assigned" or self.state == "done" or self.state == "cancel") \
               and self.picking_type_id.code == "incoming" and self.purchase_line_id

    def set_props(self, unlink=False):
        posupplyplan = """
                <posupplyplan>
                  <DocEntry>{}</DocEntry>
                  <Version>{}</Version>
                  <LineNum>{}</LineNum>
                  <ItemCode>{}</ItemCode>
                  <Quantity>{}</Quantity>
                  <ShipDate>{}</ShipDate>
                </posupplyplan>
            """

        self.xml = posupplyplan.format(
            self.picking_id.id,                                         # DocEntry
            tools.format_date(output_date_format='%Y%m%d%H%M%S'),       # Version
            self.id,                                                    # LineNum
            self.product_id.default_code or self.product_id.id,         # ItemCode
            self.product_uom_qty if self.state == "assigned" else 0,    # Quantity
            tools.format_date(self.date_expected)                       # ShipDate
        )

        self.obj_type = '20'
