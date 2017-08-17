# -*- coding: utf-8 -*-
from .pd_base import BaseExtClass
from .. import tools


class PurchaseOrderLine(BaseExtClass):
    _inherit = "purchase.order.line"

    fields_to_watch = ('order_id', 'id', 'product_id', 'product_qty', 'qty_received', 'date_planned', 'state')

    def is_notifiable(self):
        return self.state == "purchase"

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
            self.order_id.id,                                       # DocEntry
            tools.format_date(output_date_format='%Y%m%d%H%M%S'),   # Version
            self.id,                                                # LineNum
            self.product_id.default_code or self.product_id.id,     # ItemCode
            self.product_qty,                                       # Quantity
            tools.format_date(self.date_planned)                    # ShipDate
        )

        from output_helper import OutputHelper
        OutputHelper.print_text("purchase.order.line.state: {}".format(self.state))

        # PurchaseOrder = 22
        # PurchaseDeliveryNote = 20

        self.obj_type = '22'
