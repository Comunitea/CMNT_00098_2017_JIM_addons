/* DE MOMENTO NO SE USA */
odoo.define('js_addons.notify', function (require) {
    "use strict";

    console.log('[jim_addons] Notifications Init...');
    var Widget = require('web.Widget');
    //var Model = require('web.DataModel');
    //var core = require('web.core');
    //var _t = core._t;

    var NotifyManager = Widget.extend({
        init: function(parent, options) {
            this._super(parent);

            console.log('[jim_addons] Notifications widget loaded!');

            this.options = $.extend({}, {
                'wrapperId': 'notifications_area',
                'cardClass': 'notification_card'
            }, options);

            this.$panel = $('<div/>').attr('id', this.options.wrapperId);
            this.$card = $('<div/>').addClass(this.options.cardClass);
            this.$panel.appendTo(this.$el);
            return this._super();
        },
        add: function(message){
            this.$card.clone().text(message).appendTo(this.$panel);
            //this.$el.show();
        },
        remove: function(){
            this.$panel.find('.' + this.options.cardClass + ':last').remove();
            //this.$el.hide();
        }
    });

    return NotifyManager;
});
