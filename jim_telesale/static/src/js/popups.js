odoo.define('jim_telesale.popups', function (require) {
"use strict";

var TsBaseWidget = require('telesale_manage_variants.base_widgets');
var GridWidgetSuper = TsBaseWidget.GridWidget

var NewOrderWidgets = require('telesale.new_order_widgets');

var GridWidget = GridWidgetSuper.include({

    // OVERWRITED to get chained discount
    get_cell_vals: function(cell){
        var qty = this.ts_model.my_str2float( $(cell).find('input.add-qty').val() );
        var price = this.ts_model.my_str2float( $(cell).find('input.add-price').val() );

        // Is a chained discount now
        var discount = $(cell).find('input.add-discount').val();

        var vals = {
            'qty': qty,
            'price': price,
            'discount': discount,  // now represent a chained discount
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

    // OVERWRITED to set chained discount instead discount
    set_cell_vals: function(line_model, line_vals){
        line_model.set('qty', line_vals.qty);
        line_model.set('pvp', line_vals.price);

        var chained_discount = line_vals.discount
        line_model.set('chained_discount', chained_discount);

        // Calculate new discount
        var discount = this.line_widget.chained_discount2float(chained_discount)
        line_model.set('discount', discount);
        line_model.update_line_values();
    },


});

});


