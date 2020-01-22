odoo.define('js_product_images.form_widgets', function (require) {
    "use strict";

    var core = require('web.core');
    var utils = require('web.utils');
    var session = require('web.session');
    var Image = core.form_widget_registry.get('image');

    /* 
        Añade al Widget de las imágenes la opción 'no_cache', que al estar a true
        genera un número aleatorio en la URL, de esta forma se invalida la caché
        del navegador y siempre se carga de nuevo la imágen
    */

    var FieldImage = Image.include({
        render_value: function() {
            // Si la opción no_cache está a true y tiene un valor y es un "attachment"
            if(this.options.no_cache && this.get('value') && utils.is_bin_size(this.get('value'))) {
                this.placeholder = session.url('/web/image', {
                    model: this.view.dataset.model,
                    id: JSON.stringify(this.view.datarecord.id || null),
                    field: (this.options.preview_image)? this.options.preview_image : this.name,
                    // Generamos el número aleatorio
                    unique: Math.round(Math.random() * 100000000)
                });

                // Ponemos el valor a false para que al llamar al padre no se actualize de nuevo la URL
                this.set_value(false);
            }

            // Llamamos al padre
            this._super();
        }
    });
});
