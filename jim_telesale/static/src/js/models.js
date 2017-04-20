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
        res.push('lqdr', 'route_name')
        return res
    },
});

// Orderline exists inside a collection, no possible to inherit trivially, so..
// Overwrite to add global_stock_available, lqdr, route, chained_discount
TsModels.Orderline.prototype.initialize = function(options){
    this.set({
        n_line: '',
        code: '',
        product: '',
        qty: 1,
        unit: '',
        pvp: 0,
        total: 0,
        //to calc totals
        margin: 0,
        taxes_ids: [],
        discount: 0.0,
        // ADD NEW FIELDS
        global_available_stock: 0.0,
        lqdr: '',
        route: '',
        chained_discount: 0.0
    });
    this.ts_model = options.ts_model;
    this.order = options.order;
    this.selected = false;
}

// Overwraited to get chained_discount
TsModels.Orderline.prototype.export_as_JSON = function(){
        var product_id = this.ts_model.db.product_name_id[this.get('product')];
        var uom_id = this.ts_model.db.unit_name_id[this.get('unit')];
        return {
            product_id:  product_id,
            qty: this.get('qty'),
            product_uom: uom_id,
            price_unit: this.get('pvp'),
            tax_ids: this.get('taxes_ids'),
            discount: this.get('discount') || 0.0,
            chained_discount: this.get('chained_discount') || '0.0'
        };
}


// No funciona, están dentro de una coleección y eso no le gusta
// Lo ideal era de esta manera pero con métodos super
// TsModels.Orderline = TsModels.Orderline.extend({
//     initialize: function(options) {
//         debugger;
//     },
//     export_as_JSON: function() {
//         debugger;
//     },
// });

// Funciona a medias, solo para la primera instancia
// TsModels.Order = TsModels.Order.extend({
//     initialize: function(options) {
//         debugger;
//         var res = OrderSuper.prototype.initialize.call(this,options);
//         this.a = new TsModels.Orderline({ts_model: this.ts_model, order:this})
//         return res
//     },
//     exportAsJSON: function(){
//         debugger;
//         var res = OrderSuper.prototype.exportAsJSON.call(this,{});
//         return res
//     },
// });

});
