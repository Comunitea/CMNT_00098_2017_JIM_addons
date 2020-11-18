odoo.define('jim_telesale.new_order_widgets2', function (require) {
"use strict";
var Model = require('web.DataModel');
var NewOrderWidgets = require('telesale.new_order_widgets');
var core = require('web.core');
var _t = core._t;

var OrderWidget = NewOrderWidgets.OrderWidget.include({
    create_line_from_vals: function(product_id, line_vals){
        var added_line = this.create_line_empty(product_id);
        added_line.set('qty', line_vals.qty || 1.0);
        added_line.set('pvp', line_vals.price || 0.0);
        added_line.set('discount', line_vals.discount || 0.0);
        added_line.set('taxes_ids', line_vals.tax_ids || []);
        added_line.update_line_values();
        return added_line;
    },

    // Creates a line with product and unit seted
    create_line_empty: function(product_id){
        var added_line = this._super(product_id);
        var product_obj = this.ts_model.db.get_product_by_id(product_id);
        var description = product_obj.display_name;
        if (product_obj.description_sale){
            description = description + '\n' + product.description_sale
        }
        added_line.set('description', description);
        return added_line;
    },

});

var OrderlineWidget = NewOrderWidgets.OrderlineWidget.include({

    // Link change chained discount to method
    set_input_handlers: function() {
        this._super();
        this.$('.col-chained_discount').change(_.bind(this.set_value, this, 'chained_discount'));
        this.$('.col-chained_discount').focus(_.bind(this.click_handler, this, 'chained_discount'));

        this.$('.col-description').blur(_.bind(this.set_value, this, 'description'));
        this.$('.col-description').focus(_.bind(this.click_handler, this, 'description'));

        this.$('.col-note').blur(_.bind(this.set_value, this, 'note'));
        this.$('.col-note').focus(_.bind(this.click_handler, this, 'note'));
    },


    // Convert a chained discout like (10.5+20) in a float (20.5)
    // or returns false if something wrong.
    chained_discount2float: function(value){
        if (!value){
            return 0.0
        }
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

    // Manage chained_discount
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
        if (key == 'qty'){
            return;
        }

        this._super(key);

        if (key == 'template'){
            var value = this.$('.col-'+key).val();
            // Case name not valid
            var template_obj = this.get_template();
          
            // Get product from model
            if (template_obj){
                var description = template_obj.display_name;
                this.model.set('description', description);
            }
            
        }

    },

    // OVERWRITED Get global stock available in product_id change
    call_product_id_change: function(product_id, add_qty){
        var self = this;

        if (!add_qty){
            add_qty = 1.0
        }

        var customer_id = self.ts_model.db.partner_name_id[self.order.get('partner')];
        var pricelist_id = self.ts_model.db.pricelist_name_id[self.order.get('pricelist')];
        var model = new Model("sale.order.line");
        return model.call("ts_product_id_change", [product_id, customer_id, pricelist_id], self.ts_model.get_user_ctx())
        .then(function(result){
            var product_obj = self.ts_model.db.get_product_by_id(product_id);
            var uom_obj = self.ts_model.db.get_unit_by_id(product_obj.uom_id)
            var description = result.name;
            if (product_obj.description_sale){
                description = description + '\n' + product.description_sale
            }
            self.model.set('description', description);
            self.model.set('code', product_obj.default_code || "");
            self.model.set('product', product_obj.display_name || "");
            self.model.set('taxes_ids', result.tax_id || []); //TODO poner impuestos de producto o vacio
            self.model.set('unit', self.model.ts_model.db.unit_by_id[result.product_uom].name);
            self.model.set('qty', add_qty);
            self.model.set('discount', result.discount || 0.0);
            self.model.set('chained_discount', result.chained_discount || '0.00');
            self.model.set('standard_price', result.standard_price, 0.0);
            self.model.set('pvp', self.ts_model.my_round( result.price_unit));

            var subtotal = self.model.get('pvp') * self.model.get('qty') * (1 - self.model.get('discount') / 100.0)
            self.model.set('total', self.ts_model.my_round(subtotal || 0,2));

            // ADDED
            self.model.set('global_available_stock', result.global_available_stock || 0.0)

            self.refresh('qty');
            self.$('.col-qty').select();
            return result 
        });
    },

    renderElement: function() {
        // Set lqdr route_name and global_available_stock
        var prod_name = this.model.get("product");
        // var prod_name = this.$('.col-product').val();
        var product_id = this.ts_model.db.product_name_id[prod_name];
        var product_obj = false
        if (product_id){
            product_obj = this.ts_model.db.get_product_by_id(product_id);
        }
        // Get first vatiant related
        else{
            var template_obj = this.get_template();
            if (template_obj){
                product_id = template_obj.product_variant_ids[0];
                product_obj = this.ts_model.db.get_product_by_id(product_id)
            }
        }

        // Always set lqdr route name and description.
        if (product_obj){
            var lqdr = (product_obj.lqdr)  ? _t("Yes") : _t("No")

            this.model.set('lqdr', lqdr);
            this.model.set('route_name', product_obj.route_name);
        }

        //set handler for fiscount plus field.
        this._super();
    },
    control_arrow_keys: function(){
        var self=this;
        this._super()
        this.$('.col-chained_discount').keydown(function(event){
          var keyCode = event.keyCode || event.which;
          if (keyCode == 40) {  // KEY DOWWN (40)
                event.preventDefault();
                $(this).parent().parent().next().find('.col-chained_discount').select();

            }
            else if (keyCode == 38){  //KEY UP
                event.preventDefault();
                $(this).parent().parent().prev().find('.col-chained_discount').select();
            }
        });
    },
});

var DataOrderWidget = NewOrderWidgets.DataOrderWidget.include({
    // fUllOverwrited to show warning  orblocking menssage menssagge and neutral documente
    // Maybe an improvement geting warning mode and message from the customer
    // and calling super after do the warning checks
    renderElement: function () {
        var self=this;
        this._super();
        this.$('#neutral').blur(_.bind(this.set_neutral_value, this, 'neutral'))
        this.$('#scheduled_order').blur(_.bind(this.set_scheduled_order, this, 'scheduled_order'))
        var current_order = this.ts_model.get('selectedOrder')
        var neutral_document = current_order.get('neutral');
        if (neutral_document) {
            this.$('#neutral').prop('checked', true);
        }
        var scheduled_order = current_order.get('scheduled_order');
        if (scheduled_order) {
            this.$('#scheduled_order').prop('checked', true);
        }
        this.$('#epd').blur(_.bind(this.set_epd_value, this, 'epd'))
        var early_payment_discount = current_order.get('epd');
    },
    set_neutral_value: function(key) {
        var value = this.$('#' + key).is(':checked');
        this.order_model.set(key, value);
    },
    set_scheduled_order: function(key) {
        var value = this.$('#' + key).is(':checked');
        this.order_model.set(key, value);
    },
    set_epd_value: function(key) {
        var value = this.$('#' + key).val();
        this.order_model.set(key, value);
    },

    perform_onchange: function(key, value) {
        var self=this;
        if (!value) {return;}
        if (key == "partner"){
            var partner_id = self.ts_model.db.partner_name_id[value];

            // Not partner found in backbone model
            if (value && !partner_id){
                var alert_msg = _t("Customer name '" + value + "' does not exist");
                alert(alert_msg);
                self.order_model.set('partner', "");
                self.refresh();
                self.$('#partner').focus();
            }
            else {
                var partner_obj = self.ts_model.db.get_partner_by_id(partner_id);
                var model = new Model("sale.order");
                model.call("ts_onchange_partner_id", [partner_id], self.ts_model.get_user_ctx())
                .then(function(result){
                    var cus_name = self.ts_model.getComplexName(partner_obj);
                    self.order_model.set('partner', cus_name);
                    self.order_model.set('partner_code', partner_obj.ref ? partner_obj.ref : "");

                    self.order_model.set('customer_comment', partner_obj.comment);
                    // TODO nan_partner_risk migrar a la 10
                    // self.order_model.set('limit_credit', self.ts_model.my_round(partner_obj.credit_limit,2));
                    // self.order_model.set('customer_debt', self.ts_model.my_round(partner_obj.credit,2));

                    self.order_model.set('comercial', partner_obj.user_id ? partner_obj.user_id[1] : (self.ts_model.get('user') ? self.ts_model.get('user').name : ""));
                    var partner_shipp_obj = self.ts_model.db.get_partner_by_id(result.partner_shipping_id);
                    var shipp_addr =self.ts_model.getComplexName(partner_shipp_obj);
                    self.order_model.set('shipp_addr', shipp_addr);
                    var pricelist_obj = self.ts_model.db.pricelist_by_id[result.pricelist_id];
                    if (pricelist_obj){
                        self.order_model.set('pricelist', pricelist_obj.name);
                    }
                    self.order_model.set('epd', result.early_payment_discount);
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
                    // if (self.order_model.get('partner')){
                    //     $('#vua-button').click();
                    // }
                    if(self.order_model.get('orderLines').length == 0 && self.order_model.get('partner')){
                        $('.add-line-button').click()
                    }
                    else{
                        self.$('#date_order').focus();
                    }

                });
            }
        }
        else if (key == "pricelist"){
            var pricelist_id = self.ts_model.db.pricelist_name_id[value];

            // Not partner found in backbone model
            if (!pricelist_id){
                var alert_msg = _t("Pricelist name '" + value + "' does not exist");
                alert(alert_msg);
                self.order_model.set('pricelist', "");
                self.refresh();
                self.$('#pricelist').focus();
            }
        }
    },
});

var TotalsOrderWidget = NewOrderWidgets.TotalsOrderWidget.include({
    no_more_clicks: function(){
        this._super();
        this.$('.proforma-button').prop('disabled', true);
        this.$('.print-alm-button').prop('disabled', true);
        this.$('.act-qty-available').prop('disabled', true);
    },
    enable_more_clicks: function(){
        this._super();
        this.$('.proforma-button').prop('disabled', false);
        this.$('.print-alm-button').prop('disabled', false);
        this.$('.act-qty-available').prop('disabled', false);
    },
    renderElement: function(){
        var self=this;
        this._super();
        this.$('.proforma-button').click(function (){ self.no_more_clicks(); self.promoCurrentOrder();});
        this.$('.print-alm-button').click(function (){ self.no_more_clicks(); self.printAlmOrder();});
        this.$('.act-qty-available').click(function (){ self.no_more_clicks(); self.actQtyAvailable();});
    },
     doPrintAlm: function(erp_id){
            this.do_action({
                model: 'sale.order',
                context: {'active_ids': [erp_id]},
                data: null,
                name: 'Quotation / Order',
                report_file: 'custom_documents.custom_sale_order_report_warehouse',
                report_name: 'custom_documents.custom_sale_order_report_warehouse',
                report_type: 'qweb-pdf',
                type: 'ir.actions.report.xml'
            });
            this.enable_more_clicks();
        },
    printAlmOrder: function() {
        var self = this;
        self.ts_model.ready3 = $.Deferred();
        self.print_id = false
        var current_order = this.ts_model.get('selectedOrder')
        if (current_order.get('erp_id') && current_order.get('erp_state') != 'draft'){
            self.doPrintAlm(current_order.get('erp_id'));

        }
        else{
            this.ts_widget.new_order_screen.totals_order_widget.saveCurrentOrder()
            $.when( self.ts_model.ready3 )
            .done(function(){
                var currentOrder = self.ts_model.get('selectedOrder')
                self.doPrint(currentOrder.get('erp_id'));
            });
        }   
    },

    promoCurrentOrder: function() {
        var self = this;
        var currentOrder = this.order_model;
        if ( (currentOrder.get('erp_state')) && (currentOrder.get('erp_state') != 'draft') ){
            alert(_t('You cant set proform state to an order which state is diferent than draft.'));
            self.enable_more_clicks();
            return;
        }
        self.saveCurrentOrder(true)
        $.when( self.ts_model.ready2 )
        .done(function(){
            if (self.ts_model.last_sale_id){
                var domain = [['id', '=', self.ts_model.last_sale_id]]
            }
            else{
                var domain = [['chanel', '=', 'telesale'], ['user_id', '=', self.ts_model.get('user').id]]
            }
            var loaded = self.ts_model.fetch('sale.order', ['id', 'name'], domain)
                .then(function(orders){
                    if (orders[0]) {
                      (new Model('sale.order')).call('ts_action_proforma',[orders[0].id])
                          .fail(function(unused, event){
                              //don't show error popup if it fails
                              console.error('Failed confirm order: ',orders[0].name);
                          })
                          .done(function(){
                            var my_id = orders[0].id
                            $.when( self.ts_widget.new_order_screen.order_widget.load_order_from_server(my_id) )
                            .done(function(){
                                self.ts_model.last_sale_id = false
                            })
                            .fail(function(){
                                self.ts_model.last_sale_id = false
                            });
                          });
                    }
                });
         });
    },

    //actQtyAvailable
    actQtyAvailable: function(){

        var self = this;
        var currentOrder = this.order_model;
        var current_order = self.ts_model.get('selectedOrder')
        var order_id = self.ts_model.get('selectedOrder').get('erp_id')
        if (!order_id){return}
        self.saveCurrentOrder(true)
        $.when(self.ts_model.ready2)
        .done(function(){
        (new Model('sale.order')).call('ts_act_qty_available',[order_id])
            .fail(function(unused, event){
              //don't show error popup if it fails
               self.enable_more_clicks();
            })
            .done(function(res){
                // LOAD THE ORDER
                self.ts_model.get('selectedOrder').destroy();
                $.when(self.ts_widget.new_order_screen.order_widget.load_order_from_server(order_id))
                    .done(function(){
                    self.ts_model.last_sale_id = false
                    self.ts_model.ready3.resolve()
                    })
                .fail(function(){
                    self.ts_model.last_sale_id = false
                    self.ts_model.ready3.reject()
                    });

                });
        })


    },



    // Allways apply promotion when apply to server
    saveCurrentOrder: function(avoid_load) {
        var current_order = this.ts_model.get('selectedOrder')
        current_order.set('set_promotion', true)
        this._super(avoid_load);
    },
        // Checks risk before puting into lqdr state or pending
    // OVERWRITED
    confirmCurrentOrder: function() {
        var self = this;
        var currentOrder = this.order_model;
        currentOrder.set('action_button', 'save')
        if ( (currentOrder.get('erp_state')) && (currentOrder.get('erp_state') != 'draft') ){
            alert(_t('You cant confirm an order which state is diferent than draft.'));
            self.enable_more_clicks();
            return;
        }
        self.saveCurrentOrder(true)
        $.when( self.ts_model.ready2 )
        .done(function(){
            if (self.ts_model.last_sale_id){
                var domain = [['id', '=', self.ts_model.last_sale_id]]
            }
            else{
                var domain = [['chanel', '=', 'telesale'], ['user_id', '=', self.ts_model.get('user').id]]
            }
            var loaded = self.ts_model.fetch('sale.order', ['id', 'name'], domain)
                .then(function(orders){
                    if (orders[0]) {
                        //CHECK RISK
                        (new Model('sale.order')).call('get_risk_msg',[orders[0].id])
                        .fail(function(unused, event){
                            //don't show error popup if it fails
                            self.ts_model.last_sale_id = false
                        })
                        .done(function(msg){
                            
                            var skip = true;
                            if (msg){
                                var skip = confirm(msg)
                            }
                            // IF NO MSG OR SKIP MSG WE CONFIRM THE ORDER
                            if (skip){
                                (new Model('sale.order')).call('confirm_order_from_ui',[orders[0].id], {'context': {'bypass_risk': true}})
                                .fail(function(unused, event){
                                  //don't show error popup if it fails
                                   self.ts_model.last_sale_id = false
                                })
                                .done(function(res){
                                    // LOAD THE ORDER
                                    var my_id = orders[0].id
                                    $.when( self.ts_widget.new_order_screen.order_widget.load_order_from_server(my_id) )
                                        .done(function(){
                                            self.ts_model.last_sale_id = false
                                        })
                                        .fail(function(){
                                            self.ts_model.last_sale_id = false
                                    });
                                });

                            }
                            // IF RISK AND NOT SKIPPED, NO CONFIRM, BUT LOAD THE ORDER AGAIN
                            else {
                                var my_id = orders[0].id
                                $.when( self.ts_widget.new_order_screen.order_widget.load_order_from_server(my_id) )
                                    .done(function(){
                                        self.ts_model.last_sale_id = false
                                    })
                                    .fail(function(){
                                        self.ts_model.last_sale_id = false
                                });
                            }

                        });

                    }
                });
         });
    },

});


});
