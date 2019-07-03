odoo.define('js_categorization.web_kanban_gauge', function (require) {
    "use strict";

    var core = require('web.core');
    var PercentPie = core.form_widget_registry.get('percentpie');
    var _t = core._t;

    var JsPercentPie = PercentPie.extend({
        render_value: function(){
            this._super();

            var value = this.get_value();
            var $o_pie = this.$el.find('.o_pie');
            $o_pie.attr('data-value', value);

            if (value == 100){
                $o_pie.find('span').text(_t('All Filled'));
                this.$pie_value.html('<i class="fa fa-check"></i>');
            }
        }
    });

    core.form_widget_registry.add('js_percentpie', JsPercentPie);

    return {
        JsPercentPie : JsPercentPie
    };

});
