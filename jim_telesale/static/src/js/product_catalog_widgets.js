odoo.define('jim_telesale.product_catalog_widgets', function (require) {
"use strict";

var Catalog = require('telesale.ProductCatalog');
var TsModels = require('telesale.models');
var core = require('web.core');
var _t = core._t;

var ProductCatalogWidget = Catalog.ProductCatalogWidget.include({

    // Get values from catalog vals to create a new line
    get_create_line_vals: function(product_id, catalog_vals, mode){
        var res = this._super(product_id, catalog_vals, mode)
        if (mode != 'template_variants')
            $.extend(res, {global_available_stock: catalog_vals.global_available_stock})

        var product_obj = this.ts_model.db.get_product_by_id(product_id);
        //var description = product_obj.name;
        var description = product_obj.display_name;
        if (product_obj.description_sale){
            description = description + '\n' + product.description_sale
        }
        $.extend(res, {description: description})
        return res
    },

    get_line_vals: function(line){
        var vals = this._super(line);
        var chained_discount = $(line).find('#add-discount').val();
        // Calculate new discount
        var discount = this.chained_discount2float(chained_discount)
        vals.discount = discount
        vals.chained_discount = chained_discount
        return vals
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

    // OVERWRITED TO CHECK CHAINED DISCOUNT VALUE
    check_chained_discount(input_field){
        var value = $(input_field).val();
        var discount = this.chained_discount2float(value)

        if (!discount){
            alert(value + _t("is not a valid format for chained discount. It must be something like 23+5.2+1"));
            $(input_field).val("0.00");
            $(input_field).focus();
            $(input_field).select();
        }
    },


    bind_onchange_events: function(){
        var self = this;
        this._super();
        this.$('.add-discount').unbind();
        this.$('.add-discount').bind('change', function(event){
             self.check_chained_discount(this);
        });
        this.$('.add-qty').unbind();
        this.$('.add-qty').bind('change', function(event){
             self.check_float(this);
             //self.call_product_uom_change(this);
        });
    },

    catalog_update_product(line_cid, line_vals){
        this._super();
        var line_model = this.get_line_model_by_cid(line_cid);
        if (line_model){
            line_model.set('discount', line_vals.discount || 0.0);
            line_model.set('chained_discount', line_vals.chained_discount || '0.0');
        }
    },


});

var ProductLineWidget = Catalog.ProductLineWidget.include({
     //OVERWRITED BECAUSE CHAINED DISCOUNT
      update_product: function(product){
        var updated_product = product;
        var line_cid = this.get_line_cid_related(product);
        updated_product['line_cid'] = line_cid;
        var taxes_str = product.tax_ids.map(String).join();
        updated_product['taxes'] = taxes_str;
        if (line_cid){
            var line_model = this.get_line_model_by_cid(line_cid);
            if (line_model){
                updated_product['qty'] = line_model.get('qty') || 0.0;
                updated_product['price'] = line_model.get('pvp') || 0.0;
                // CHAINED DISCOUNT
                updated_product['discount'] = line_model.get('discount') || 0.0;
                updated_product['chained_discount'] = line_model.get('chained_discount') || '0.0';
            }
        }
        return updated_product
    },

});

});



