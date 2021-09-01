# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ProductTemplate(models.Model):

    _inherit = "product.template"

    delivery_cost = fields.Boolean()


#TODO: MIgrar de ser necesario
# ~ class ProductProduct(models.Model):

    # ~ _inherit = "product.product"

    # ~ def _compute_partner_ref(self):
        # ~ for supplier_info in self.seller_ids:
            # ~ if supplier_info.name.id == self._context.get("partner_id"):
                # ~ product_name = supplier_info.product_name or self.default_code
        # ~ else:
            # ~ variable_attributes = self.attribute_line_ids.mapped(
                # ~ "attribute_id"
            # ~ )
            # ~ variant = self.product_template_attribute_value_ids._variant_name(
                # ~ variable_attributes
            # ~ )
            # ~ product_name = (
                # ~ variant and "%s (%s)" % (self.name, variant) or self.name
            # ~ )
        # ~ self.partner_ref = "%s%s" % (
            # ~ self.code and "[%s] " % self.code or "",
            # ~ product_name,
        # ~ )

    # ~ def name_get(self):
        # ~ """
        # ~ Se sobreescribe la funcion para que salga el nombre de la variante
        # ~ en productos con 1 unico atributo
        # ~ """
        # ~ # TDE: this could be cleaned a bit I think
        # ~ # res = super(ProductProduct, self).name_get()
        # ~ def _name_get(d):
            # ~ name = d.get("name", "")
            # ~ code = (
                # ~ self._context.get("display_default_code", True)
                # ~ and d.get("default_code", False)
                # ~ or False
            # ~ )
            # ~ if code:
                # ~ name = "[%s] %s" % (code, name)
            # ~ return (d["id"], name)

        # ~ partner_id = self._context.get("partner_id")
        # ~ if partner_id:
            # ~ partner_ids = [
                # ~ partner_id,
                # ~ self.env["res.partner"]
                # ~ .browse(partner_id)
                # ~ .commercial_partner_id.id,
            # ~ ]
        # ~ else:
            # ~ partner_ids = []

        # ~ # all user don't have access to seller and partner
        # ~ # check access and use superuser
        # ~ self.check_access_rights("read")
        # ~ self.check_access_rule("read")
        # ~ result = []
        # ~ for product in self.sudo():
            # ~ # display only the attributes with multiple possible values on the template
            # ~ variable_attributes = product.attribute_line_ids.mapped(
                # ~ "attribute_id"
            # ~ )
            # ~ variant = product.product_template_attribute_value_ids._variant_name(
                # ~ variable_attributes
            # ~ )
            # ~ name = (
                # ~ variant and "%s (%s)" % (product.name, variant) or product.name
            # ~ )
            # ~ sellers = []
            # ~ if partner_ids:
                # ~ sellers = [
                    # ~ x
                    # ~ for x in product.seller_ids
                    # ~ if (x.name.id in partner_ids) and (x.product_id == product)
                # ~ ]
                # ~ if not sellers:
                    # ~ sellers = [
                        # ~ x
                        # ~ for x in product.seller_ids
                        # ~ if (x.name.id in partner_ids) and not x.product_id
                    # ~ ]
            # ~ if sellers:
                # ~ for s in sellers:
                    # ~ seller_variant = (
                        # ~ s.product_name
                        # ~ and (
                            # ~ variant
                            # ~ and "%s (%s)" % (s.product_name, variant)
                            # ~ or s.product_name
                        # ~ )
                        # ~ or False
                    # ~ )
                    # ~ mydict = {
                        # ~ "id": product.id,
                        # ~ "name": seller_variant or name,
                        # ~ "default_code": s.product_code or product.default_code,
                    # ~ }
                    # ~ temp = _name_get(mydict)
                    # ~ if temp not in result:
                        # ~ result.append(temp)
            # ~ else:
                # ~ mydict = {
                    # ~ "id": product.id,
                    # ~ "name": name,
                    # ~ "default_code": product.default_code,
                # ~ }
                # ~ result.append(_name_get(mydict))
        # ~ return result
