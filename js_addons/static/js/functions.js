odoo.define('js_addons.fixedTableHeaders', function (require) {
    "use strict";

    console.log('[js_addons] JS Addons Init...');

    var ListView = require('web.ListView');
    var fixedTablesActive = false;

    $.fn.hasScrollBar = function() {
        return this[0] ? this[0].scrollHeight > this.innerHeight() : false;
    }

    $.fn.scrollEnds = function() {
        return (this.scrollTop() + this.innerHeight() >= this[0].scrollHeight);
    }

    $.isStandaloneListView = function() {
        var $container = $('div.o_view_manager_content:not(.o_form_field)');
        // Is standalone view if: (CONTAINER EXITS) AND (BUTTON ".o_cp_switch_list" EXISTS AND HAS CLASS "active") AND (CONTAINER CHILD NOT HAS CLASS "o_form_view")
        return ($container.length === 1 && $('button.o_cp_switch_list.active').length === 1 && $container.children('div.o_form_view').length === 0);
    }

    $.scrollIndicator = function() {
        var $indicator = $('#fixed-table-scroll-indicator');
        if (!$indicator.length) $indicator = $('<div id="fixed-table-scroll-indicator" title="Hay más elementos ¡haz scroll!"><div></div></div>').appendTo($('div.o_view_manager_content:not(.o_form_field)')).hide();
        return $indicator;
    }

    $.fixTableButton = function() {
        var $container = $('div.o_cp_right');
        $container.find('div.btn-fxt-toggle').remove();
        var $newBtn = $('<div class="btn-group btn-group-sm o_cp_switch_buttons btn-fxt-toggle"/>');
        $('<button type="button" class="btn btn-icon fa fa-lg fa-toggle-off" data-original-title="Cabecera"></button>').appendTo($newBtn).tooltip();
        return $newBtn.appendTo($('div.o_cp_right'));
    }

    $.setTableHeaderFixedIfActive = function() {
        // Tables to apply
        var $tableObj = $('div.o_view_manager_content:not(.o_form_field)').find('table');
        var $tableBody = $tableObj.find('tbody');

        if (fixedTablesActive){
            // Activate fixed header
            $tableObj.addClass('fixed-table-header');
            // If has scroll
            if ($tableBody.hasScrollBar()){
                $.scrollIndicator().fadeIn('slow');
                $tableBody.scroll(function() {
                    // If scroll reaches end
                    if ($tableBody.scrollEnds()) $.scrollIndicator().fadeOut('slow');
                });
            }
        }else{
            // Deactivate fixed header
            $tableObj.removeClass('fixed-table-header');
            $.scrollIndicator().fadeOut('fast');
        }
    }

    ListView.include({
        reload_content: function(){
            var self = this;

            $('div.o_cp_switch_buttons, div.o_sub_menu_content, nav.oe_main_menu_navbar').off().click(function(){
                // Workaround to remove toggle button
                $.fixTableButton().remove();
            });

            this._super().then(function(){
                // Set toggle btn on o_control_panel
                if ($.isStandaloneListView()){
                    $.fixTableButton().click(function(){
                        fixedTablesActive = !fixedTablesActive;
                        $.setTableHeaderFixedIfActive();
                    });
                }else $.fixTableButton().remove();
                // Set table fixed if is active
                $.setTableHeaderFixedIfActive();
            });
        }
    });
});
