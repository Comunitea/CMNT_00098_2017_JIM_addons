odoo.define('jim_telesale.product_catalog_widgets', function (require) {
"use strict";

var Catalog = require('telesale.ProductCatalog');
var TsModels = require('telesale.models');
// var core = require('web.core');
// var _t = core._t;

var ProductCatalogWidget = Catalog.ProductCatalogWidget.include({

    // Get values from catalog vals to create a new line
    get_create_line_vals: function(product_id, catalog_vals, mode){
        var res = this._super(product_id, catalog_vals, mode)
        if (mode != 'template_variants')
            $.extend(res, {global_available_stock: catalog_vals.global_available_stock})

        var product_obj = this.ts_model.db.get_product_by_id(product_id);
        var description = product_obj.name;
        if (product_obj.description_sale){
            description = description + '\n' + product.description_sale
        }
        $.extend(res, {description: description})
        return res
    },

    // get_line_vals: function(line){
    //     var vals = this._super(line);
    //     var global_stock_str =  line.getAttribute('stock') || "0.00"
    //     var global_stock = this.ts_model.my_str2float( global_stock_str );
    //     $.extend(vals, {global_available_stock: global_stock})
    //     return vals
    // },

});

});



