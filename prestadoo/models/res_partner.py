# -*- coding: utf-8 -*-
from .pd_base import BaseExtClass


class Partner(BaseExtClass):
    _inherit = "res.partner"

    fields_to_watch = ('id', 'name', 'vat', 'email', 'web_password', 'property_product_pricelist', 'active', 'type',
                       'parent_id', 'street', 'zip', 'city', 'country_id', 'company_id', 'vip_web_access')

    def is_notifiable(self):
        # En res.partner se almacenan tanto las empresas, como empresas "hijas" (del mismo grupo), como contactos y
        # direcciones. Para saber si un registro es notificable debemos comprobar que el 'commercial_partner_id' (es
        # la primera empresa (is_company == True) padre recorriendo el árbol de abajo arriba), salvo que se trate de
        # un registro diferente, en cuyo caso solamente se notificará si es una dirección de envío. Por tanto:
        #
        #   - Comprobamos que commercial_partner_id (que es la empresa "padre") cumpla que:
        #       * sea empresa (is_company == True)
        #       * sea cliente (customer == True)
        #       * tenga correo y contraseña
        #   - En el campo 'vip_web_access' se indique que el cliente tiene acceso web para alguna empresa del grupo
        #
        # Si cumple los requisitos, notificamos si commercial_partner_id == id, es decir, se trata de un registro de
        # tipo "empresa padre"; en caso contrario, puede ser un contacto, una dirección de envío, una dirección de
        # facturación u otro tipo (other), así que notificamos sólo si type == 'delivery'.
        if self.commercial_partner_id.is_company \
                and self.commercial_partner_id.customer \
                and self.commercial_partner_id.email \
                and self.commercial_partner_id.web_password:

            if self.commercial_partner_id.id == self.id:
                self.fields_to_watch = ('id', 'name', 'vat', 'email', 'web_password', 'property_product_pricelist',
                                        'active', 'type', 'parent_id', 'company_id', 'vip_web_access')
                return True
            else:
                self.fields_to_watch = ('name', 'active', 'type', 'parent_id', 'street', 'zip', 'city', 'country_id',
                                        'company_id')
                return self.type == 'delivery'

        return False

    def set_props(self, unlink=False):
        pocustomer = """
                <pocustomer>
                  <CardCode>{}</CardCode>
                  <CardName>{}</CardName>
                  <CntctPrsn>{}</CntctPrsn>
                  <LicTradNum>{}</LicTradNum>
                  <E_Mail>{}</E_Mail>
                  <Password>{}</Password>
                  <validFor>{}</validFor>
                  <ListNum>{}</ListNum>
                </pocustomer>
              """
        pocustomeraddress = """
                <pocustomeraddress>
                  <CardCode>{}</CardCode>
                  <LineNum>{}</LineNum>
                  <Address>{}</Address>
                  <DefaultAddress>{}</DefaultAddress>
                  <Street>{}</Street>
                  <Block>{}</Block>
                  <ZipCode>{}</ZipCode>
                  <City>{}</City>
                  <Country>{}</Country>
                </pocustomeraddress>
            """

        # El filtro de notificaciones viene hecho ya en "is_notifiable", de forma que aquí llegarán IC's o
        # direcciones de entrega
        if self.commercial_partner_id.id == self.id: # Se trata de un IC
            pricelist_list = []
            valid = 'Y'
            if self.vip_web_access: # Si está asignado a alguna empresa del grupo
                # Recorremos la lista de compañías a las que puede tener acceso el IC para averiguar sus tarifas
                for company in self.vip_web_access:
                    if self.env.user.company_id.id == company.id:
                        pricelist = self.property_product_pricelist
                    else:
                        pricelist_obj = self.env['product.pricelist']
                        pricelist_id = pricelist_obj.sudo()._get_partner_pricelist(
                            self.id, company.id)
                        pricelist = pricelist_obj.browse(pricelist_id)
                    if pricelist.legacy_code:
                        pricelist_code = pricelist.legacy_code
                    else:
                        pricelist_code = str(pricelist.id + 1000)
                    pricelist_list.append(str(company.id) + ',' + pricelist_code)
                    if not unlink and self.active:
                        if pricelist.name == 'SIN PRECIO':
                            valid = 'P'
                    else:
                        valid = 'N'
            else:
                valid = 'N'

            self.xml = pocustomer.format(
                    self.ref or self.id,                   # CardCode
                    self.name,                             # CardName
                    self.default_contact_person or '',     # CntctPrsn
                    self.vat or '',                        # LicTradNum
                    self.email,                            # E_Mail
                    self.web_password,                     # Password
                    valid,                                 # validFor
                    ';'.join(pricelist_list))              # ListNum

            self.obj_type = '2'

        else: # Se trata de una dirección
            if not unlink and self.active:
                valid = 'Y'
            else:
                valid = 'N'

            self.xml = pocustomeraddress.format(
                    self.parent_id.ref or self.parent_id.id,    # CardCode
                    self.legacy_code or '#' + str(self.id),     # LineNum
                    self.name,                                  # Address
                    '-1' if valid == 'N' else '1',              # DefaultAddress
                    self.street or '',                          # Street
                    self.street2 or '',                         # Block
                    self.zip or '',                             # ZipCode
                    self.city or '',                            # City
                    self.country_id.code or '')                 # Country

            self.obj_type = 'ADDRESS'
