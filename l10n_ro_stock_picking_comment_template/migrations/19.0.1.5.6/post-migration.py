# Copyright 2026 NextERP Romania SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Drop the legacy duplicate title from the reception / delivery comments.

The before-lines comments for the goods receipt note and the delivery aviz used
to carry an ``<h2>`` title ("Notă de Intrare si Recepție" / "Aviz de Însoțire a
Mărfii") that repeated the report title. The title is now printed once by the
report itself and the ``<h2>`` was removed from the comment source. On an
existing database the old value survives in the stored (translated) ``text``
field, so the title still prints twice — this strips the leading ``<h2>…</h2>``
from those two records in every installed language. The intentional titles on
the consume-voucher / usage-giving comments are left untouched.
"""
import re

from odoo import SUPERUSER_ID, api

_H2 = re.compile(r"\s*<h2>.*?</h2>\s*", re.S)
_XMLIDS = (
    "l10n_ro_stock_picking_comment_template.l10n_ro_picking_in_up",
    "l10n_ro_stock_picking_comment_template.l10n_ro_picking_delivery_internTransfer",
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    langs = [code for code, _name in env["res.lang"].get_installed()]
    for xmlid in _XMLIDS:
        record = env.ref(xmlid, raise_if_not_found=False)
        if not record:
            continue
        for lang in langs:
            rec = record.with_context(lang=lang)
            text = rec.text or ""
            new_text = _H2.sub("", text, count=1)
            if new_text != text:
                rec.text = new_text
