# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.exceptions import AccessError
from odoo.addons.jesie.jesie import Jesie
from output_helper import OutputHelper, MsgTypes


class BaseExtClass(models.Model):
    # Instanciamos una variable _inherit de Odoo para luego sobreescribirla
    _inherit = 'product.product'
    # _inherit = None

    xml = None
    obj_type = None
    fields_to_watch = None

    def must_notify(self, vals):
        # Solamente debemos notificar las operaciones que se produzcan si el usuario está logado en JIM SPORTS
        # if self.env.user.company_id.id != 1:
        #     return False

        # Según lo hablado con Miguel (y parece que lo acordado en Jim con Óscar), debemos utilizar el company_id del
        #  objeto, no del contexto, porque parece ser que van a modificar y/o crear maestros (incluso documentos)
        # desde una empresa para otras empresas.

        # No todos los objetos tienen company_id (product.tag, product.attribute, ... no tienen)
        if hasattr(self, 'company_id'):
            if self.company_id and self.company_id.id != 1:
                return False

        # Comprobamos si existe alguna función que nos indique si debemos modificar o no. Si no existe, continuamos.
        is_notifiable = getattr(self, "is_notifiable", None)
        if callable(is_notifiable):
            if not is_notifiable():
                return False

        if self.fields_to_watch and vals:
            fields = sorted(list(set(vals).intersection(set(self.fields_to_watch))))

            return len(fields) > 0

        # Si no hay ningún campo a monitorizar entonces SIEMPRE notificamos
        return True

    def sanitize_xml(self):
        self.xml = self.xml.replace('&', '\u0026')

    @api.model
    def create(self, vals):
        try:
            res = super(BaseExtClass, self).create(vals)

            if self.must_notify(vals):
                res.set_props()
                res.sanitize_xml()

                Jesie.write('A', res.obj_type, res.id, res.xml)

                OutputHelper.print_text("- oper_type: {}"
                                        "\n\t- obj_type: {}"
                                        "\n\t- obj_key: {}"
                                        "\n\t- xml: {}"
                                        .format('A', res.obj_type, res.id, res.xml), MsgTypes.OK)

        except Exception as ex:
            raise AccessError("Error capturing 'create' event.\nTry again later.\n\nError: {}".format(ex))

        return res

    @api.multi
    def write(self, vals):
        res = True

        try:
            for item in self:
                res = super(BaseExtClass, item).write(vals)

                if item.must_notify(vals):
                    item.set_props()
                    item.sanitize_xml()

                    Jesie.write('U', item.obj_type, item.id, item.xml)

                    OutputHelper.print_text("- oper_type: {}"
                                            "\n\t- obj_type: {}"
                                            "\n\t- obj_key: {}"
                                            "\n\t- xml: {}"
                                            .format('U', item.obj_type, item.id, item.xml), MsgTypes.OK)

                    post_write = getattr(item, "post_write", None)
                    if callable(post_write):
                        post_write()

        except Exception as ex:
            raise AccessError("Error capturing 'write' event.\nTry again later.\n\nError: {}".format(ex))

        return res

    @api.multi
    def unlink(self):
        try:
            for item in self:
                if item.must_notify(None):
                    item.set_props(unlink=True)
                    item.item.sanitize_xml()

                    Jesie.write('D', item.obj_type, item.id, item.xml)

                    OutputHelper.print_text("- oper_type: {}"
                                            "\n\t- obj_type: {}"
                                            "\n\t- obj_key: {}"
                                            "\n\t- xml: {}"
                                            .format('D', item.obj_type, item.id, item.xml), MsgTypes.OK)

            res = super(BaseExtClass, self).unlink()

        except Exception as ex:
            raise AccessError("Error capturing 'unlink' event.\nTry again later.\n\nError: {}".format(ex))

        return res
