odoo.define('jim_telesale.new_order_widgets2', function (require) {
"use strict";
var Model = require('web.DataModel');
var NewOrderWidgets = require('telesale.new_order_widgets');
var core = require('web.core');
var _t = core._t;

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
    set_input_handlers: function() {
        this._super();
        this.$('.col-chained_discount').change(_.bind(this.set_value, this, 'chained_discount'));
        this.$('.col-chained_discount').focus(_.bind(this.click_handler, this, 'chained_discount'));
    },
    renderElement: function() {
        // Set lqdr route_name and global_available_stock
        var prod_name = this.$('.col-product').val();
        var product_id = this.ts_model.db.product_name_id[prod_name];
        if (product_id){
            var product_obj = this.ts_model.db.get_product_by_id(product_id);
            var lqdr = (product_obj.lqdr)  ? _t("Yes") : _t("No")
            this.model.set('lqdr', lqdr);
            this.model.set('route_name', product_obj.route_name);
        }
        //set handler for fiscount plus field.
        this._super();
    },

    // Convert a chained discout like (10.5+20) in a float (20.5)
    // or returns false if something wrong.
    chained_discount2float: function(value){
        var split_disc = value.split('+')
        var discount = 0.0
        var disc = 0 
        for (var i in split_disc){
            disc = split_disc[i]
            if (isNaN(disc) || disc == "") {
               return false // Break
            }
            else{
              discount = discount + parseFloat(disc);
            }
        }
        return discount;

    },
    set_value: function(key) {
        this._super(key)
        if (key == 'chained_discount'){
            var value = this.$('.col-chained_discount').val();

            var discount = this.chained_discount2float(value);
            if (!discount){
                alert(value + _t("is not a valid format for chained discount. It must be something like 23+5.2+1"));
                this.model.set('discount', 0.0);
                this.model.set('chained_discount', 0.0);
            }
            else{
                this.model.set('discount', discount);
            }
            this.refresh('chained_discount');  
        }
    },
    perform_onchange: function(key){
        if (key == 'pvp'){
            this.refresh('chained_discount');
        }
        this._super(key);
    }
});

var DataOrderWidget = NewOrderWidgets.DataOrderWidget.include({
    // Overwrited to show warning  orblocking menssage menssagge
    // Maybe an improvement geting warning mode and message from the customer
    // and calling super after do the warning checks
    perform_onchange: function(key, value) {
        var self=this;
        if (!value) {return;}
        if (key == "partner"){
            var partner_id = self.ts_model.db.partner_name_id[value];

            // Not partner found in backbone model
            if (!partner_id){
                var alert_msg = _t("Customer name '" + value + "' does not exist");
                alert(alert_msg);
                self.order_model.set('partner', "");
                self.refresh();
            }
            else {
                var partner_obj = self.ts_model.db.get_partner_by_id(partner_id);
                var model = new Model("sale.order");
                model.call("ts_onchange_partner_id", [partner_id])
                .then(function(result){
                    var cus_name = self.ts_model.getComplexName(partner_obj);
                    self.order_model.set('partner', cus_name);
                    self.order_model.set('partner_code', partner_obj.ref ? partner_obj.ref : "");
                    
                    self.order_model.set('customer_comment', partner_obj.comment);
                    // TODO nan_partner_risk migrar a la 10
                    // self.order_model.set('limit_credit', self.ts_model.my_round(partner_obj.credit_limit,2));
                    // self.order_model.set('customer_debt', self.ts_model.my_round(partner_obj.credit,2));

                    self.order_model.set('comercial', partner_obj.user_id ? partner_obj.user_id[1] : "");
                    var partner_shipp_obj = self.ts_model.db.get_partner_by_id(result.partner_shipping_id);
                    var shipp_addr =self.ts_model.getComplexName(partner_shipp_obj);
                    self.order_model.set('shipp_addr', shipp_addr);

                    // Get alert if warning is not false
                    if (result.warning){
                        alert(result.warning);
                        if (result.mode == 'block'){
                            self.order_model.set('partner', "");
                        }
                        
                    }
                    self.refresh();
                    // New line and VUA button when chang
                    // Only do it when partner is setted
                    if (self.order_model.get('partner')){
                        $('#vua-button').click();
                    }
                    if(self.order_model.get('orderLines').length == 0 && self.order_model.get('partner')){
                        $('.add-line-button').click()
                    }
                    else{
                        self.$('#date_order').focus();
                    }

                });
            }
        }
    },
});

});


