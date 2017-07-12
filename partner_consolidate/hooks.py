# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import logging


logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """
    Drop original commercial_partner_id (related field) from account_invoice
    model in order to replace and recalculate the new  computed field
    commercial_partner_id
    """
    logger.info('PRE INIT HOOK: Started')
    logger.info('Droping commercial_partner_id column from account_invoice')
    cr.execute("""ALTER TABLE account_invoice
                  DROP COLUMN commercial_partner_id CASCADE;""")
    logger.info('PRE INIT HOOK: finished')
