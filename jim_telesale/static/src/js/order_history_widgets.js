odoo.define('jim_telesale.order_history_widgets2', function (require) {
"use strict";

var NewOrderWidgets = require('telesale.new_order_widgets');

var OrderWidget = NewOrderWidgets.OrderWidget.include({

    // Get chained_discount and description to the line
    get_line_fields: function(){
        var res = this._super();
        res.push('chained_discount', 'name')
        return res
    },
});

});

