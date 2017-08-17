# -*- coding: utf-8 -*-
from .pd_base import BaseExtClass


class ProductAttribute(BaseExtClass):
    _inherit = "product.attribute"

    def is_notifiable(self):
        return not self.is_color

    def set_props(self, unlink=False):
        xml = """
                <potallaje>
                  <Code>{}</Code>
                  <Name>{}</Name>
                </potallaje>
              """

        self.xml = xml.format(
            self.legacy_code or '#' + str(self.id),    # Code
            self.name                       # Name
        )
        self.obj_type = 'TALLAJE'
