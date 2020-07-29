# -*- coding: utf-8 -*-
# © 2019 Jim Sports Group
{
	'name': 'JS B2B',
	'version': '10.0.1.0',
	'author': 'Jim Sports',
	'category': 'Connector',
	'website': 'https://jimsports.com',
	'summary': 'Odoo JSync Connector',
	'description': '''
		Conector para sincronizar datos con otras plataformas/clientes.
		Transmite los datos por HTTP a un servidor secundario que los procesa.
	''',
	'license': 'AGPL-3',
	'depends': [
		'web',
		'base',
		'sale',
		'product',
		'product_brand',
		'product_tags',
		'jim_sale',
		#'jim_addons',
		#'js_categorization',
		#'prices_export',
		#'stock_export'
	],
	'qweb': [
		'static/xml/widgets.xml',
		'static/xml/base.xml'
	],
	'data': [
		'security/ir.model.access.csv',
		'data/item_data_out.xml',
		'data/item_data_in.xml',
		'data/web_category.xml',
		'data/ir_cron.xml',
		'views/res_partner.xml',
		'views/product.xml',
		'views/product_pricelist.xml',
		'views/assets.xml',
		'views/settings.xml',
		'views/item_out.xml',
		'views/item_in.xml',
		'views/export.xml',
		'views/reports.xml',
		'views/res_users.xml'
	],
	'external_dependencies': {
		'python' : [
			'barcodenumber',
			'unidecode',
			'requests',
			'httplib2',
			'urllib3'
		]
	},
	'contributors': [
		"Pablo Luaces <pablo@jimsports.com>",
	],
	'post_init_hook': 'post_init_actions',
	'application': True,
	'installable': True
}