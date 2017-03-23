odoo.define('jim_telesale.new_order_widgets2', function (require) {
"use strict";

var Model = require('web.DataModel');
var NewOrderWidgets = require('telesale.new_order_widgets');

var ProductInfoOrderWidget = NewOrderWidgets.ProductInfoOrderWidget.include({
    set_default_values: function(){
        this._super();
        this.route = ""; 
        this.lqdr = "";
    },
    change_product: function(){
        this._super();
        var self = this
        var line_product = this.selected_line.get("product")
        self.n_line = self.selected_line.get('n_line') + " / " + self.ts_model.get('selectedOrder').get('orderLines').length;
        if (line_product != ""){
            var product_id = this.ts_model.db.product_name_id[line_product]
            var partner_name = this.ts_model.get('selectedOrder').get('partner');
            var partner_id = this.ts_model.db.partner_name_id[partner_name];
            if (product_id && partner_id){
                var model = new Model('product.product');
                model.call("get_product_info",[product_id,partner_id])
                    .then(function(result){
                        self.route = result.route;
                        self.lqdr = result.lqdr;
                        self.renderElement();
                    });
            }   
        }
    },
    });
});

