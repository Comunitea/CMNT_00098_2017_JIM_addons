# -*- coding: utf-8 -*-
from .pd_base import BaseExtClass


class ProductTemplate(BaseExtClass):
    _inherit = "product.template"

    fields_to_watch = ('id', 'default_code', 'template_code', 'name', 'barcode', 'description', 'web_global_stock',
                       'product_brand_id', 'attribute_line_ids', 'tag_ids', 'active', 'type', 'company_id')

    def is_notifiable(self):
        return self.type == "product" and self.tag_ids

    def set_props(self, unlink=False):
        poitem = """
                <poitem>
                  <ItemCode>{}</ItemCode>
                  <ItemName>{}</ItemName>
                  <CodeBars>{}</CodeBars>
                  <UserText>{}</UserText>
                  <Model>{}</Model>
                  <Tallaje>{}</Tallaje>
                  <Talla>{}</Talla>
                  <Color>{}</Color>
                  <Stock>{}</Stock>
                  <SWeight1>{}</SWeight1>
                  <FirmName>{}</FirmName>
                  <Price>{}</Price>
                  <ItmsGrpCod>{}</ItmsGrpCod>
                  <validFor>{}</validFor>
                </poitem>
              """

        def get_tallaje_attribute_id():
            """ Con esta función obtenemos el id del primer atributo que NO sea Color
            porque, según lo hablado con Miguel, los atributos o son Color (y sólo debe haber uno) o tallaje """
            for attr in self.attribute_line_ids:
                if not attr.attribute_id.is_color:
                    return attr.attribute_id.legacy_code or '#' + str(attr.attribute_id.id)

        if unlink:
            is_active = 'N'
        else:
            is_active = 'Y' if self.active else 'N'

        tallaje = get_tallaje_attribute_id()

        self.xml = poitem.format(
            self.template_code or self.default_code or self.id,     # ItemCode
            self.name,                                              # ItemName
            '',                                                     # CodeBars
            self.description or '',                                 # UserText
            '',                                                     # Model
            tallaje or '',                                          # Tallaje
            '',                                                     # Talla
            '',                                                     # Color
            self.global_available_stock or '0.0',                   # Stock
            '0.0',                                                  # Sweight1
            self.product_brand_id.name or '',                       # FirmName
            '0.0',                                                  # Price
            ";".join(tag.legacy_code or '#' + str(tag.id) for tag in self.tag_ids),  # ItmsGrpCod
            is_active                                               # validFor
        )

        self.obj_type = '4'

    def post_write(self):
        if len(self.product_variant_ids) > 1:
            for prod in self.product_variant_ids:
                # Utilizamos 'active' como dummy para poder llamar a .write()
                prod.write({'active': prod.active})
