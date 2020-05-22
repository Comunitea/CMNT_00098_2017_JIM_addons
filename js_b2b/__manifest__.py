# -*- coding: utf-8 -*-
# © 2019 Jim Sports Group
{
	'name': 'JS B2B',
	'version': '10.0.1.0',
	'author': 'Jim Sports',
	'category': 'Connector',
	'website': 'https://jimsports.com',
	'summary': 'Permite extraer datos de los modelos de Odoo y enviarlos a otro servidor',
	'description': 'Conector para sincronizar datos con otras plataformas/clientes. Envía los datos por HTTP a un servidor secundario que los procesa y crea un punto de entrada para recibir datos',
	'license': 'AGPL-3',
	'depends': [
		'base',
		'sale',
		'product',
		'product_brand',
		'product_tags',
		'jim_sale',
		'js_categorization'
		#'prices_export',
		#'stock_export'
	],
	'qweb': [
		'static/xml/widgets.xml',
	],
	'data': [
		'security/ir.model.access.csv',
		'data/item_data_out.xml',
		'data/item_data_in.xml',
		'views/res_partner.xml',
		'views/product.xml',
		'views/assets.xml',
		'views/settings.xml',
		'views/item_out.xml',
		'views/item_in.xml'
	],
	'contributors': [
		"Pablo Luaces <pablo@jimsports.com>",
	],
	'application': False,
	'installable': True
}