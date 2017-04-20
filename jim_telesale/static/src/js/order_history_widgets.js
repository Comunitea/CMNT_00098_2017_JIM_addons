odoo.define('jim_telesale.order_history_widgets2', function (require) {
"use strict";

var OrderHistory = require('telesale.OrderHistory');

var HistorylineWidget = OrderHistory.HistorylineWidget.include({
    get_line_fields: function(){
        var res = this._super();
        res.push('chained_discount')
        return res
    },
});

});


