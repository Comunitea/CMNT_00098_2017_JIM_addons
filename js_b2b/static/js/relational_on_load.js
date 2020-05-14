odoo.define('js_b2b.relational_on_load', function (require) {
    "use strict";

    var form_relational = require('web.form_relational');

    form_relational.FieldMany2One.include({
        render_editable: function () {
            var self = this;
            $.when(self._super()).then(function(){
                if (!self.get('effective_readonly') && self.options.relational_on_load){
                    self.$input.trigger(self.options.relational_on_load);
                }
            });
        },
    });

    /*form_relational.FieldX2Many.include({
        load_views: function () {
            var self = this;
            $.when(self._super()).then(function(){
                if (!self.get('effective_readonly') && self.options.relational_on_load){
                    self.$input.trigger(self.options.relational_on_load);
                }
            });
        },
    });*/

});
