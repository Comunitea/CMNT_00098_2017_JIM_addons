odoo.define('jim_telesale.models2', function (require) {
"use strict";
var TsModels = require('telesale.models');
var TsModelSuper = TsModels.TsModel
var OrderLineSuper = TsModels.OrderLine
var OrderSuper = TsModels.Order
var Backbone = window.Backbone;



// Only a TsModel, so no problem to extend and add funcionality
TsModels.TsModel = TsModels.TsModel.extend({
    _get_product_fields: function(){
        var res = TsModelSuper.prototype._get_product_fields.call(this,{});
        res.push('lqdr', 'route_name', 'description_sale', 'name')
        return res
    },

    // To set it to line in function build_order_create_lines
    get_line_vals: function(line, order_model){
        var res = TsModelSuper.prototype.get_line_vals.call(this, line, order_model);
        res.chained_discount = line.chained_discount || '0.00';
        res.description = line.name || '0.00';
        return res
    }
});

// Set template to store the template name en la linea
var _initialize_ = TsModels.Orderline.prototype.initialize;
TsModels.Orderline.prototype.initialize = function(options){
    var self = this;
    this.set({
        global_available_stock:  options.global_available_stock ||0.0,
        lqdr:  options.lqdr ||'',
        description:  options.description ||'',
        route:  options.route ||'',
        chained_discount:  options.chained_discount || 0.0
    });

    //template_singe: A normal line, template with one variant
    //template_variants: Grouping line with special grouping behavior
    //variant: Line created with the grid, parent line is a template_variants
    return _initialize_.call(this, options);
}


// Overwraited to get chained_discount
var _exportJSON_ = TsModels.Orderline.prototype.export_as_JSON;
TsModels.Orderline.prototype.export_as_JSON = function(){
    var res = _exportJSON_.call(this, {});
    var to_add = {chained_discount: this.get('chained_discount') || '0.0',
                  description: this.get('description')}
    res = $.extend(res, to_add)
    return res
}

});
