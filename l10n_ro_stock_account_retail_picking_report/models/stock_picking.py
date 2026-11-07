# Copyright (C) 2026 NextERP Romania
# Copyright (C) 2026 Dakai Soft SRL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    l10n_ro_retail_incoming = fields.Boolean(
        string="Reception Into a Shop",
        compute="_compute_l10n_ro_retail_incoming",
        store=True,
        help="At least one line brings goods into a retail location from "
        "outside it. Such a transfer prints as a reception note showing the "
        "cost, the markup and the shelf price.",
    )

    @api.depends(
        "move_ids.location_id",
        "move_ids.location_dest_id",
        "move_ids.location_id.l10n_ro_retail",
        "move_ids.location_dest_id.l10n_ro_retail",
    )
    def _compute_l10n_ro_retail_incoming(self):
        """True when goods actually cross into a shop.

        Read on the moves rather than on the picking's own locations: a
        putaway rule can send the lines of one transfer to several places, and
        the picking header then says nothing useful about where the goods
        ended up.

        The retail flag of those locations is part of what this depends on,
        not just the locations themselves. A warehouse is routinely marked
        retail after it has been trading for a while, and every transfer made
        before that day went on printing without its reception note title -
        the locations had not changed, only what they are.
        """
        for picking in self:
            picking.l10n_ro_retail_incoming = any(
                move.location_dest_id.l10n_ro_retail
                and not move.location_id.l10n_ro_retail
                for move in picking.move_ids
            )

    def _l10n_ro_show_valued_columns(self):
        """Hide the plain valued columns on a retail reception.

        The retail note prints its own money columns (purchase price/value,
        markup, shelf price with and without VAT, deferred VAT). Left on, the
        valued columns (unit price, additional charges, subtotal, taxes, total)
        print alongside them and the table grows to a dozen-odd columns of
        which half are zero. The retail layout wins whenever goods enter a
        shop."""
        res = super()._l10n_ro_show_valued_columns()
        return res and not self.l10n_ro_retail_incoming
