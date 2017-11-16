odoo.define('jim_telesale.popups', function (require) {
"use strict";

var TsBaseWidget = require('telesale_manage_variants.popups');
var GridWidgetSuper = TsBaseWidget.GridWidget

var NewOrderWidgets = require('telesale.new_order_widgets');
var core = require('web.core');
var _t = core._t;

var GridWidget = GridWidgetSuper.include({

    // OVERWRITED to get chained discount and global_stock
    get_cell_vals: function(cell){
        var qty = this.ts_model.my_str2float( $(cell).find('input.add-qty').val() );
        var price = this.ts_model.my_str2float( $(cell).find('input.add-price').val() );
        // Is a chained discount now
        var global_available_stock = this.ts_model.my_str2float($(cell).find('#stock_div').attr('stock-value'));
        var discount = $(cell).find('input.add-discount').val();

        var col_id = $(cell).attr('col-id');
        var row_id = $(cell).attr('row-id');
        var cell_obj = this.get_cell_obj(col_id, row_id)
        var vals = {
            'qty': qty,
            'price': price,
            'discount': discount,  // now represent a chained discount
            'stock': global_available_stock,  // to write in orderLine
            'tax_ids': cell_obj.tax_ids,
            'enable': cell_obj.enable
        }
        return vals
    },
    
    // INHERIT Recover chained-discount instead of discount from model;
    update_cell: function(cell){
        var updated_cell = this._super(cell);

        var line_cid = updated_cell['line_cid']

        updated_cell['discount'] = '0.00'  // Server return float, now always string.
        if (line_cid){
            var line_model = this.get_line_model_by_cid(line_cid);
            if (line_model){
                updated_cell['discount'] = line_model.get('chained_discount') || '0.00'
            }
        }
        return updated_cell
    },

    // OVERWRITED to set chained discount instead discount and global_stock
    set_cell_vals: function(line_model, line_vals){
        line_model.set('qty', line_vals.qty);
        line_model.set('pvp', line_vals.price);

        var chained_discount = line_vals.discount
        line_model.set('chained_discount', chained_discount);

        // Calculate new discount
        var discount = this.line_widget.chained_discount2float(chained_discount)
        line_model.set('discount', discount);
        line_model.set('global_available_stock', line_vals.stock);
        line_model.set('taxes_ids', line_vals.tax_ids || []); 
        line_model.set('to_update', true); 
        line_model.update_line_values();
    },

    // OVERWRITED TO CHECK CHAINED DISCOUNT VALUE
    check_chained_discount(input_field){
        var value = $(input_field).val();
        var discount = this.line_widget.chained_discount2float(value)

        if (!discount){
            alert(value + _t("is not a valid format for chained discount. It must be something like 23+5.2+1"));
            $(input_field).val("0.00");
            $(input_field).focus();
            $(input_field).select();
        }
    },


    bind_onchange_events: function(){
        this._super();
        this.$('.add-discount').unbind();
        this.$('.add-discount').bind('change', function(event){
             self.check_chained_discount(this);
        });
    },


});

});


