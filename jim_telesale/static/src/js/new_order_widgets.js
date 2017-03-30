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
    // Full overwrited to get global_available_stock
    call_product_id_change: function(product_id){
        var self = this;
        $.when( self.update_stock_product(product_id) ).done(function(){
            var customer_id = self.ts_model.db.partner_name_id[self.order.get('partner')];
            var model = new Model("sale.order.line");
            model.call("ts_product_id_change", [product_id, customer_id])
            .then(function(result){
                var product_obj = self.ts_model.db.get_product_by_id(product_id);
                var uom_obj = self.ts_model.db.get_unit_by_id(product_obj.uom_id[0])
            
                self.model.set('code', product_obj.default_code || "");
                self.model.set('product', product_obj.display_name || "");
                self.model.set('taxes_ids', result.tax_id || []); //TODO poner impuestos de producto o vacio
                self.model.set('unit', self.model.ts_model.db.unit_by_id[result.product_uom].name);
                self.model.set('qty', result.product_uom_qty);
                self.model.set('discount', 0.0);
                self.model.set('pvp', self.ts_model.my_round( result.price_unit));
                self.model.set('global_available_stock', self.ts_model.my_round( result.global_available_stock));
               
                var subtotal = self.model.get('pvp') * self.model.get('qty') * (1 - self.model.get('discount') / 100.0)
                self.model.set('total', self.ts_model.my_round(subtotal || 0,2));
                self.refresh('qty');
                self.$('.col-qty').select()
            });
        })
        .fail(function(){
            // alert(_t("NOT WORKING"));
        })
    },
    renderElement: function(){
        //Because i dont know how to add to Backbone orderline defaults.
        // this.model.set('global_available_stock', 0.0)
        this._super();
        var self = this;
        var product_name = self.model.get('product')
    },

});

});


