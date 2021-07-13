# © {year} {company}
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class ReportProductLabelFromPurchase(models.AbstractModel):
    _name = "report.custom_documents.product_from_purchase_label_report"

    @api.model
    def render_html(self, docids, data=None):
        purchase = self.env["purchase.order"].browse(docids)
        product_ids = purchase.mapped("order_line.product_id.id")
        products = self.env["product.product"].browse(product_ids)
        product_list = []
        product_page = []
        for product in products:
            product_page.append(product)
            if len(product_page) == 8:
                product_list.append(product_page)
                product_page = []
        if len(product_page):
            product_list.append(product_page)
        docargs = {
            "doc_ids": product_ids,
            "doc_model": "product.product",
            "docs": products,
            "product_list": product_list,
        }
        return self.env["report"].render(
            "custom_documents.product_label_report", docargs
        )


class ReportProductLabelFromSale(models.AbstractModel):
    _name = "report.custom_documents.product_from_sale_label_report"

    @api.model
    def render_html(self, docids, data=None):
        purchase = self.env["sale.order"].browse(docids)
        product_ids = purchase.mapped("order_line.product_id.id")
        products = self.env["product.product"].browse(product_ids)
        product_list = []
        product_page = []
        for product in products:
            product_page.append(product)
            if len(product_page) == 8:
                product_list.append(product_page)
                product_page = []
        if len(product_page):
            product_list.append(product_page)
        docargs = {
            "doc_ids": product_ids,
            "doc_model": "product.product",
            "docs": products,
            "product_list": product_list,
        }
        return self.env["report"].render(
            "custom_documents.product_label_report", docargs
        )


class ReportProductLabelFromProduct(models.AbstractModel):
    _name = "report.custom_documents.product_from_product_label_report"

    @api.model
    def render_html(self, docids, data=None):

        products = self.env["product.product"].browse(docids)
        product_list = []
        product_page = []
        for product in products:
            product_page.append(product)
            if len(product_page) == 8:
                product_list.append(product_page)
                product_page = []
        if len(product_page):
            product_list.append(product_page)
        docargs = {
            "doc_ids": docids,
            "doc_model": "product.product",
            "docs": products,
            "product_list": product_list,
        }
        return self.env["report"].render(
            "custom_documents.product_label_report", docargs
        )


class ReportProductLabelFromProductNeutral(models.AbstractModel):
    _name = "report.custom_documents.product_label_neutral"

    @api.model
    def render_html(self, docids, data=None):

        products = self.env["product.product"].browse(docids)
        product_list = []
        product_page = []
        for product in products:
            product_page.append(product)
            if len(product_page) == 8:
                product_list.append(product_page)
                product_page = []
        if len(product_page):
            product_list.append(product_page)
        docargs = {
            "doc_ids": docids,
            "doc_model": "product.product",
            "docs": products,
            "product_list": product_list,
        }
        return self.env["report"].render(
            "custom_documents.product_label_report_neutral", docargs
        )
