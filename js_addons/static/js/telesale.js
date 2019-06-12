odoo.define('js_addons.telesale', function (require) {
    "use strict";

    console.log('[jim_addons] Telesale Init...');
    //var Model = require('web.DataModel');
    var NewOrderWidgets = require('telesale.new_order_widgets');
    const discontinuedItemBg = '#ff4a4a';
    //var core = require('web.core');
    //var _t = core._t;

    NewOrderWidgets.OrderlineWidget.include({

        // EXTENDED
        call_product_id_change: function(product_id, add_qty){
            var self = this;

            self._super(product_id, add_qty).then(function(result){
                // CHANGE BG ON DISCONTINUED PRODUCTS
                if (typeof(result.discontinued) != 'undefined' && result.discontinued){
                    var $item_note = $('<tr><td colspan="13">Tenga en cuenta que este producto está descatalogado</td></tr>');
                    $item_note.css('background', discontinuedItemBg).insertAfter(self.$el);
                    self.$el.css('background', discontinuedItemBg);
                    // BORRAR
                    window.last_order_line = self;
                }
            });
        }

    });
});
