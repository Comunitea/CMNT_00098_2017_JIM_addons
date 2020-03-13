# -*- coding: utf-8 -*-
# © 2019 Jim Sports Group
{
	'name': 'JS B2B',
	'version': '10.0.1.0',
	'author': 'Jim Sports',
	'category': 'Connector',
	'website': 'https://jimsports.com',
	'description': 'Conector para sincronizar datos con otras plataformas/clientes. Envía los datos por HTTP a un servidor secundario que los procesa y recibe datos de Google Pub/Sub.',
	'license': 'AGPL-3',
	'qweb': [
		'static/xml/widgets.xml',
	],
	'data': [
		'security/ir.model.access.csv',
		'data/item_data.xml',
		'views/product.xml',
		'views/assets.xml',
		'views/settings.xml',
		'views/item_out.xml',
		'views/item_in.xml'
	],
	'depends': [
		'base',
		'sale',
		'jim_sale',
		'product_tags',
		'js_product_images',
		'purchase',
		'sga_file',
		'product_code_generator'
	],
	'contributors': [
		"Pablo Luaces <pablo@jimsports.com>",
	],
	'application': False,
	'installable': True
}
