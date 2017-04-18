odoo.define('jim_telesale.models2', function (require) {
"use strict";
var TsModels = require('telesale.models');

// Overwrite backbone TsModel function to get extra fields lqdr and route_name;
TsModels.TsModel.prototype._get_product_fields = function(){
    return  ['display_name', 'default_code', 'list_price', 'standard_price', 'uom_id', 'taxes_id', 'weight', 'lqdr', 'route_name']}
});
