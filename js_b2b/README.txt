
	       ________  ___   _____ ____  ____  ____  ___________
	      / /  _/  |/  /  / ___// __ \/ __ \/ __ \/_  __/ ___/
	 __  / // // /|_/ /   \__ \/ /_/ / / / / /_/ / / /  \__ \ 
	/ /_/ // // /  / /   ___/ / ____/ /_/ / _, _/ / /  ___/ / 
	\____/___/_/  /_/   /____/_/    \____/_/ |_| /_/  /____/  
                                                          

DESCRIPCIÓN
===========

Este módulo mantiene sincronizada una base de datos secundaria (Postgres) con una estructura diferente a la de Odoo enviando peticiones POST por protocolo HTTP a otro servidor a la vez que gestiona las configuraciones que envían o reciben esos datos.

VERSIONES SOPORTADAS (Probadas)
===============================

* Python 2.7
* Odoo 10 CE

REQUISITOS
==========

Este módulo requiere las siguientes librerías de python, para instalarlas acceder al sandbox y ejecutar el comando: pip install -r module/requirements.txt
o bien pip install -librería- por cada una de ellas

* urllib3 >= 1.25.3
* httplib2 >= 0.13.1
* Unidecode >= 1.1.1
* requests >= 2.22.0
* gtin-validator >= 1.0.3

Para poder utilizar este módulo es necesario que un servidor secundario ejecute el módulo de Pyhton 3 "jsync" y esté a la escucha

CONFIGURACIÓN
=============

Enlazaremos este módulo con el servidor secundario mediante la configuración del mismo, Configuración -> B2B -> Settings -> JSync URL

También cambiaremos los datos del FTP público si es necesario, este se usa para publicar las imágenes de Marcas, Categorías y Productos

Después podemos modificar las configuraciones para cada modelo de Odoo en "Items Out" e "Items In", esta configuración es un tanto especial y sólo debe hacerla una persona con conocimientos de programación, ya que hay que escribir una parte de código. El motivo de hacerlo así fué poder realizar cambios en producción sin necesidad de reiniciar el servidor.

Todas las variables y métodos que se definan en esta configuración pasarán a un diccionario llamado b2b en tiempo de ejecución, por lo tanto si definimos un nuevo método ej. "def test_method(param):" para llamarlo usaremos b2b['test_method'](param)".

-- CAMBIOS EN LA BASE DE ODOO --

En Odoo 10 el tamaño de las imágenes grandes está hardcodeado en el fichero odoo/tools/image.py línea 140 y se ha cambiado a 1920 para que se puedan pasar con más resolución