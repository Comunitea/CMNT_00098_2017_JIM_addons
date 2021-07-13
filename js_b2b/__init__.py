# POR COMPATIBILIDAD CON EL ANTIGUO PRESTADOO!
import sys

reload(sys)
sys.setdefaultencoding("utf8")

from . import models
from . import base
from . import controllers
