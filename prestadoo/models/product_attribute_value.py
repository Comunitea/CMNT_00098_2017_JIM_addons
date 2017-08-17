# -*- coding: utf-8 -*-
from .pd_base import BaseExtClass


class ProductAttributeValue(BaseExtClass):
    _inherit = "product.attribute.value"

    def is_notifiable(self):
        return self.code

    def set_props(self, unlink=False):
        if self.attribute_id.is_color:
            xml = """
                    <pocolor>
                      <Code>{}</Code>
                      <Name>{}</Name>
                    </pocolor>
                  """

            self.xml = xml.format(
                self.code,                      # Code
                self.name                       # Name
            )
            self.obj_type = 'COLOR'

        else:
            xml = """
                    <potalla>
                      <Code>{}</Code>
                      <Name>{}</Name>
                      <Position>{}</Position>
                      <TallajeCode>{}</TallajeCode>
                    </potalla>
                  """

            self.xml = xml.format(
                self.code,                                              # Code
                self.name,                                              # Name
                self.sequence,                                          # Position
                self.attribute_id.legacy_code or '#' + str(self.attribute_id.id)   # TallajeCode
            )
            self.obj_type = 'TALLA'
