odoo.define('js_parameterization.form_widgets', function (require) {
    "use strict";

    var core = require('web.core');
    var common = require('web.form_common');
    var FieldPercentPie = core.form_widget_registry.get('percentpie');
    var FieldMany2ManyTags = core.form_widget_registry.get('many2many_tags');
    var _t = core._t;

    var JsPercentPie = FieldPercentPie.extend({
        render_value: function(){
            this._super.apply(this, arguments);
            var value = this.get_value();
            this.$el.find('.o_pie').attr('data-value', value);

            if (value == 100){
                this.$el.find('span').text(_t('Completada'));
                this.$pie_value.html('<i class="fa fa-check"></i>');
            }
        }
    });

    var JsFieldMany2ManyTags = FieldMany2ManyTags.extend({
        get_badge_id: function(el){
            if ($(el).hasClass('badge')) return $(el).data('id');
            return $(el).closest('.badge').data('id');
        },
        events: {
            'click .o_delete': function(e) {
                e.stopPropagation();
                this.remove_id(this.get_badge_id(e.target));
            },
            'click .badge': function(e) {
                e.stopPropagation();

                if (typeof(this.many2one) == 'undefined'){
                    alert(_t("Can't open this item on view mode!"));
                    return false;
                }

                var self = this;
                var record_id = this.get_badge_id(e.target);
                new common.FormViewDialog(self, {
                    res_model: self.many2one.field.relation,
                    res_id: record_id,
                    context: self.dataset.context.add({ 'hide_fields': true }),
                    title: _t('Open: ') + self.many2one.string,
                    readonly: self.many2one.get('effective_readonly')
                }).on('write_completed', self, function() {
                    self.dataset.cache[record_id].from_read = {};
                    self.dataset.evict_record(record_id);
                    self.render_value();
                }).open();
            }
        }
    });

    core.form_widget_registry.add('js_percentpie', JsPercentPie);
    core.form_widget_registry.add('js_many2many_tags', JsFieldMany2ManyTags);

    return {
        JsPercentPie : JsPercentPie,
        JsFieldMany2ManyTags: JsFieldMany2ManyTags
    };

});
