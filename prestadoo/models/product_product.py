# -*- coding: utf-8 -*-
from .pd_base import BaseExtClass, api, OutputHelper as Console, Jesie


class ProductProduct(BaseExtClass):
    _inherit = "product.product"

    packet_size = 500

    def is_notifiable(self):
        return self.product_tmpl_id.type == "product" and \
               self.tag_ids and \
               self.default_code and \
               self.default_code.find('False') == -1 and \
               self.name.find('(copia)') == -1

    fields_to_watch = ('id', 'default_code', 'name', 'barcode', 'description', 'web_global_stock',
                       'product_brand_id', 'attribute_line_ids', 'tag_ids', 'active', 'type', 'force_web')

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

        def get_tallaje_talla_color():
            """ En base a lo hablado con Miguel, los atributos o son Color (y sólo debe haber uno) o tallaje.

                Con esta función obtenemos:
                    - el id del primer atributo de la plantilla que NO sea Color
                    - el id de la talla del tallaje obtenido
                    - el id del color
            """

            tallajeid = None
            tallajecode = None
            tallacode = None
            colorcode = None

            for attr in self.product_tmpl_id.attribute_line_ids:
                if not attr.attribute_id.is_color:
                    tallajecode = attr.attribute_id.legacy_code or '#' + str(attr.attribute_id.id)
                    tallajeid = attr.attribute_id.id
                    break

            for val in self.attribute_value_ids:
                if val.attribute_id.id == tallajeid:
                    tallacode = val.legacy_code or '#' + str(val.id)
                elif val.attribute_id.is_color:
                    colorcode = val.legacy_code or '#' + str(val.id)

                if tallacode and colorcode:
                    break

            return tallajecode, tallacode, colorcode

        if unlink or (self.force_web == 'no') or not self.active:
            is_active = 'N'
        else:
            is_active = 'N'
            for tag in self.tag_ids:
                if tag.web:
                    is_active = 'Y'
            # is_active = 'Y' if self.active else 'N'

        tallaje, talla, color = get_tallaje_talla_color()

        self.xml = poitem.format(
            self.default_code or self.id,                                   # ItemCode
            self.name,                                                      # ItemName
            self.barcode or '',                                             # CodeBars
            self.description or '',                                         # UserText
            self.product_tmpl_id.template_code or self.product_tmpl_id.default_code or self.product_tmpl_id.id,  # Model
            tallaje or '',                                                  # Tallaje
            talla or '',                                                    # Talla
            color or '',                                                    # Color
            self.web_global_stock or '0.0',                                 # Stock
            self.weight or '0.0',                                           # Sweight1
            self.product_brand_id.name or '',                               # FirmName
            self.price or '0.0',                                            # Price
            ";".join(tag.legacy_code or '#' + str(tag.id) for tag in self.tag_ids),  # ItmsGrpCod
            is_active                                                       # validFor
        )

        self.obj_type = '4'

    def get_stock_packet_size(self):
        packet_size = self.env["ir.config_parameter"].search([('key', '=', 'prestadoo.stock.packet.size')])

        if not packet_size:
            Console.debug("[Prestadoo] No se ha encontrado parámetro 'prestadoo.stock.packet.size' en 'Configuración "
                          "-> Parámetros -> Parámetros del sistema'; se utilizará 500.")
            self.packet_size = 500
        else:
            self.packet_size = int(packet_size.value)
            Console.debug("[Prestadoo] Encontrado parámetro 'prestadoo.stock.packet.size'. "
                          "Valor = {}".format(packet_size.value))

    @api.model
    def stock_2_jesie(self):
        Console.debug('[Prestadoo] Inicio de proceso de notificación de STOCK a Jesie')

        self.get_stock_packet_size()

        poitemstock = """
                        <poitemstock>
                          <ItemCode>{}</ItemCode>
                          <Stock>{}</Stock>
                        </poitemstock>
                    """

        product_list = self.search([('active', '=', True),
                                    ('sale_ok', '=', True),
                                    ('default_code', '!=', False),
                                    # ('default_code', 'not like', '%ñ%'),
                                    # ('default_code', 'not like', '%Ñ%'),
                                    ('type', '=', 'product')],
                                   order='id')

        msg_count = 0
        poitemstock_xml_list = []

        debug_sum = 0
        debug_total = str(len(product_list))

        while msg_count < len(product_list):

            products_slice = product_list[msg_count: msg_count + self.packet_size]

            poitemstock_slice_xml = "".join(poitemstock.format(product.default_code, product.web_global_stock)
                                            for product in products_slice)

            poitemstock_xml_list.append(poitemstock_slice_xml)
            msg_count += self.packet_size

            debug_sum += len(products_slice)
            Console.debug('[Prestadoo] Construído mensaje para {} items ({} de {})'.format(str(len(products_slice)),
                                                                                           str(debug_sum),
                                                                                           debug_total))

        Console.debug('[Prestadoo] Todos los mensajes construídos.\n\t\tComienza encolado en Jesie de {} '
                      'mensajes'.format(str(len(poitemstock_xml_list))))

        try:
            for idx, stock_xml in enumerate(poitemstock_xml_list):
                Jesie.write('A', 'STOCK', idx, stock_xml)

        except Exception as ex:
            Console.debug("[Prestadoo] Error writing stock: {}".format(ex))

        Console.debug('[Prestadoo] Fin de proceso de notificación de STOCK a Jesie')
