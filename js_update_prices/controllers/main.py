# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class jsUpdatePrices(http.Controller):
    @http.route([
        '/js_update_prices'
    ], type='http', auth='user')
    def index(self, **kw):
        return request.render('js_update_prices.prices_edit_index')

    @http.route([
        '/js_update_prices/run'
    ], type='http', auth='user')
    def run(self, order='', tmode=0, **kw):

        # Solo pueden acceder usuarios con permisos de configuración (Administración/Ajustes)
        if request.env.user.has_group('base.group_system'):

            numLines = 0 # Contador para numero de líneas
            test_mode = int(tmode) # Test mode como entero (0-1)
            debug_processed = [] # Creamos una lista para guardar los valores

            # Hacemos uso de request para acceder al modelo de los pedidos
            if (order != ''):
                sales = request.env['sale.order'].sudo().search([
                    ('name', '=', order)
                ], order='id')
            else:
                sales = request.env['sale.order'].sudo().search([
                    ('state', '=', 'draft')
                ], order='id')

            #import web_pdb; web_pdb.set_trace()

            # Realizamos un bucle para descargar las imágenes y guardar los resultados
            for order in sales:

                print("######################### UPDATING ORDER [" + str(order.name) + "] #########################")

                # Realizamos un bucle para recorrer las lineas del pedido
                for line in order.order_line:

                    # A veces el nombre de la línea no coincide con el producto, por eso lo actualizamos
                    line.name = line.product_id.name_get()[0][1]

                    print("LINE [" + str(line.name) + "] : " + str(line.price_unit) + " | " + str(line.price_subtotal))

                    numLines += 1

                    # Si la linea no está facturada actualizamos el importe
                    if (line.state == 'sale' and (line.invoice_status == 'no' or line.invoice_status == 'to invoice')):

                        old_price = line.price_unit
                        price_unit = order.pricelist_id.get_product_price(line.product_id, 1, order.partner_id)
                        price_subtotal = order.pricelist_id.get_product_price(line.product_id, line.product_qty, order.partner_id)

                        if (line.price_unit != price_unit):

                            # Si no estamos en modo test
                            if not test_mode:

                                # Actualizamos el precio
                                line.write({
                                    'price_unit': price_unit,
                                    'price_subtotal': price_subtotal,
                                    'price_total': price_subtotal
                                })

                                #line.template_line.product_id_change()

                            # Guardamos la linea en el listado
                            debug_processed.append({
                                'id': line.id,
                                'name': line.name,
                                'quantity': line.product_qty,
                                'old_price': old_price,
                                'new_price': price_unit
                            })

            # Pasamos los resultados a la vista
            return request.render('js_update_prices.prices_edit_batch', {
                'total': numLines,
                'total_changes': len(debug_processed),
                'products': debug_processed,
                'test_mode': test_mode
            })

        else:
            return 'No está autorizado para acceder a esta página'
