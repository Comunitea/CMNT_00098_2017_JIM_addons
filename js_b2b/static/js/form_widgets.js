odoo.define('js_b2b.form_widgets', function (require) {
    "use strict";

    var core = require('web.core');
    var form_common = require('web.form_common');
    var AceEditor = core.form_widget_registry.get('ace');
    var FieldChar = core.form_widget_registry.get('char');
    var _t = core._t;

    var FieldColor = FieldChar.extend({
        template: 'FieldColorHex'
    });

    var FieldCode = AceEditor.extend({
        template: 'FieldCode',
        willStart: function() {
            var ajax = require('web.ajax');
            return $.when(this._super()).then(function(){
                return ajax.loadJS('/web/static/lib/ace/theme-monokai.js');
            });
        },
        start: function() {
            this.$parent = this.$el.parent();
            return this._super();
        },
        initialize_content: function() {
            if (this.aceEditor) {
                // Destroy editor to prevent memory leaks
                this.aceEditor.destroy();
                this.aceEditor.container.remove();
                // Fix to reset textarea
                this.$parent.html(this.$el);
            }

            this.aceEditor = ace.edit(this.el);
            this.aceEditor.session.setMode('ace/mode/python');
            this.aceEditor.setOptions({ showPrintMargin: false, minLines:20, maxLines: 10000 });
            if (this.get('effective_readonly')) this.aceEditor.setReadOnly(true);
            else this.aceEditor.setTheme('ace/theme/monokai');
        },
        render_value: function() {
            if (this.get('value') && this.aceEditor) this.aceEditor.setValue(this.get('value'), 1);
            if (this.get('effective_readonly') && this.aceEditor) this.aceEditor.session.foldAll();
        },
        commit_value: function() {
            if (!this.get('effective_readonly') && this.aceEditor) this.set_value(this.aceEditor.getValue());
            return this._super();
        }
    });

    var FieldClipboard = FieldChar.extend({
        template: 'FieldClipboard',
        higlightField: function(){
            var self = this;

            if (self.$input){
                self.$input.css('box-shadow', '0 0 8px rgba(124,123,173,.8)');
                setTimeout(function(){
                    self.$input.css('box-shadow', 'none');
                }, 500);
            }
        },
        initialize_content: function() {
            var self = this;

            if (!this.get('effective_readonly')) {
                if (!this.$input) this.$input = this.$el.find('input');
                if (!this.$clipboard_button) this.$clipboard_button = this.$('.o_external_button');

                this.$clipboard_button.click(function(ev) {
                    ev.preventDefault();
                    self.$input.focus();
                    self.$input.select();

                    try {
                        if (document.execCommand('copy')) self.higlightField();
                    } catch (err) {
                        alert(_t('Oops, unable to copy!') + '\n' + err);
                    }
                });
            }
        },
        destroy_content: function () {
            if (this.$input) delete this.$input;
            if (this.$clipboard_button) {
                this.$clipboard_button.off('blur focus click');
                delete this.$clipboard_button;
            }
        },
    });

    var WidgetWebsiteButton = form_common.AbstractField.extend({
        template: 'WidgetWebsiteButton',
        render_value: function () {
            this._super.apply(this, arguments);
            var $value = this.$('.o_value');
            if(this.get_value() === true) $value.html(_t('Published')).removeClass('text-danger').addClass('text-success');
            else $value.html(_t('Unpublished')).removeClass('text-success').addClass('text-danger');
            if(this.node.attrs.class) this.$el.addClass(this.node.attrs.class);
        },
        is_false: function () {
            return false;
        },
    });

    core.form_widget_registry.add('js_code', FieldCode);
    core.form_widget_registry.add('js_colorpicker', FieldColor);
    core.form_widget_registry.add('js_clipboard', FieldClipboard);
    core.form_widget_registry.add('js_website_button', WidgetWebsiteButton);

    return {
        FieldCode: FieldCode, 
        FieldColor: FieldColor,
        FieldClipboard : FieldClipboard,
        WidgetWebsiteButton: WidgetWebsiteButton
    };

});
