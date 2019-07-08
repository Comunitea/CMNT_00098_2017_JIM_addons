odoo.define('js_categorization.form_widgets', function (require) {
    "use strict";

    var core = require('web.core');
    var PercentPie = core.form_widget_registry.get('percentpie');

    var JsPercentPie = PercentPie.extend({
        render_value: function(){
            this._super.apply(this, arguments);
            var value = this.get_value();
            this.$el.find('.o_pie').attr('data-value', value);

            if (value == 100){
                //this.$el.find('span').text(core._t('All Filled'));
                this.$pie_value.html('<i class="fa fa-check"></i>');
            }
        }
    });

    core.form_widget_registry.add('js_percentpie', JsPercentPie);

    return {
        JsPercentPie : JsPercentPie
    };

});
