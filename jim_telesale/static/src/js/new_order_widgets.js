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

var OrderlineWidget = NewOrderWidgets.OrderlineWidget.include({
    refresh: function(focus_key){
        /*
        Full overwrited to get the global available stock
        TODO IMPROVE, REVIEW REFRESH CALLS
        */
        var self=this;
        var price = this.model.get("pvp")
        var qty = this.model.get("qty")
        var disc = this.model.get("discount")
        var subtotal = price * qty * (1 - (disc/ 100.0))
        this.model.set('total',subtotal);
       
        
        var product_name = self.model.get('product')
        var product_id = self.ts_model.db.product_name_id[product_name]
        if(product_id) {
            var model = new Model("product.product")
            model.call("ts_get_global_stocks",[product_id])
            .then(function(result){
                self.model.set('global_available_stock', self.ts_model.my_round(result.global_available_stock));
                self.renderElement();
                self.$('.col-'+ focus_key).focus()
            })

        }
        self.renderElement();
        self.$('.col-'+ focus_key).focus()
    },
});

});


