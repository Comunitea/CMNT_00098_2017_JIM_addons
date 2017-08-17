# -*- coding: utf-8 -*-
from .pd_base import BaseExtClass


class ProductTag(BaseExtClass):
    _inherit = "product.tag"

    def set_props(self, unlink=False):
        pocategory = """
                            <pocategory>
                              <Code>{}</Code>
                              <Name>{}</Name>
                              <Visible>{}</Visible>
                            </pocategory>
                        """

        posubcategory = """
                            <posubcategory>
                              <Code>{}</Code>
                              <ItmsGrpCod>{}</ItmsGrpCod>
                              <ItmsGrpNam>{}</ItmsGrpNam>
                              <Visible>{}</Visible>
                            </posubcategory>
                        """

        if not unlink \
                and self.web \
                and self.active:
            visible = "1"
        else:
            visible = "0"

        if self.parent_id.id:
            self.xml = posubcategory.format(self.parent_id.legacy_code or '#' + str(self.parent_id.id),
                                            self.legacy_code or '#' + str(self.id),
                                            self.name,
                                            visible)
            self.obj_type = '52'
        else:
            self.xml = pocategory.format(self.legacy_code or '#' + str(self.id),
                                         self.name,
                                         visible)
            self.obj_type = 'CATEGORY'
