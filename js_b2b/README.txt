
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

Este módulo requiere las siguientes librerías de python, para instalarlas acceder al sandbox y ejecutar el comando: pip install module/requirements.txt
o bien pip install -librería- por cada una de ellas

* urllib3 >= 1.25.3
* httplib2 >= 0.13.1
* Unidecode >= 1.1.1
* requests >= 2.22.0
* barcodenumber >= 0.5.0

Para poder utilizar este módulo es necesario que un servidor secundario ejecute el módulo de Pyhton 3 "jsync" y esté a la escucha

CONFIGURACIÓN
=============

Enlazaremos este módulo con el servidor secundario mediante la configuración del mismo, Configuración -> B2B -> Settings -> JSync URL

También cambiaremos los datos del FTP público si es necesario, este se usa para publicar las imágenes de Marcas, Categorías y Productos

Después podemos modificar las configuraciones para cada modelo de Odoo en "Items Out" e "Items In", esta configuración es un tanto especial y sólo debe hacerla una persona con conocimientos de programación, ya que hay que escribir una parte de código. El motivo de hacerlo así fué poder realizar cambios en producción sin necesidad de reiniciar el servidor.

Todas las variables y métodos que se definan en esta configuración pasarán a un diccionario llamado b2b en tiempo de ejecución, por lo tanto si definimos un nuevo método ej. "def test_method(param):" para llamarlo usaremos b2b['test_method'](param)".

-- CONFIGURACIÓN ITEMS OUT --

Model Names: Nombre del modelo o modelos separados por comas de los que se obtendrán los datos
Description: Descripción de la configuración que estamos creando
Code:

	fields_to_watch = None

		Permite especificar que campos del modelo se vigilarán, si no se le pasa una lista o tupla serán todos

	def is_notifiable(self, action, vals):
		...

		Aquí debemos devolver True o False si queremos que se notifique sólo cuando el registro cumpla unas condiciones, en caso contrario True

	(opcional) def pre_data(self, action):
		...

		Acción que se ejecutará si existe antes de llamara a b2b['get_data'](record)

	def get_data(self):
		...

		Esta función deverá devolver normalmente un diccionario con los datos a enviar, aunque también puede retornar una lista de diccionarios

	(opcional) def pos_data(self, action):
		...

		Acción que se ejecutará si existe después de llamara a b2b['get_data'](record)

-- CONFIGURACIÓN ITEMS IN --

Model Names: Nombre del modelo al que se incorporarán los datos
Description: Descripción de la configuración que estamos creando
Code:

	def get_action(action, data):
		return action

		Permite cambiar la acción cuando se recibe un dato de entrada en función de unas condiciones, por defecto se pasa tal cual
		
	def get_data(self, data):
		...

		Devolverá un único diccionario de datos, que se pasará al modelo para crear el registro