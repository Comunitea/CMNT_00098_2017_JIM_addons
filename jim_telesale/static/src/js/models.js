odoo.define('jim_telesale.models2', function (require) {
"use strict";
var TsModels = require('telesale.models');
var TsModelSuper = TsModels.TsModel

TsModels.TsModel = TsModels.TsModel.extend({
    _get_product_fields: function(){
        var res = TsModelSuper.prototype._get_product_fields.call(this,{});
        res.push('lqdr', 'route_name')
        return res
    },
});


});
