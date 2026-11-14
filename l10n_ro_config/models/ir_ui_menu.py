# Copyright 2022 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class L10nRoIrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    is_l10n_ro_record = fields.Boolean()

    @api.model
    @api.ormcache(
        "frozenset(self.env.user._get_group_ids())",
        "debug",
        "self.env.company.l10n_ro_accounting",
    )
    def _visible_menu_ids(self, debug=False):
        visible = super()._visible_menu_ids(debug=debug)
        if not visible or self.env.company._check_is_l10n_ro_record():
            return visible
        ro_ids = set(
            self.env["ir.model.data"]
            .sudo()
            .search(
                [
                    ("model", "=", "ir.ui.menu"),
                    ("res_id", "in", list(visible)),
                    ("module", "=like", "l10n_ro%"),
                ]
            )
            .mapped("res_id")
        )
        return set(visible) - ro_ids
