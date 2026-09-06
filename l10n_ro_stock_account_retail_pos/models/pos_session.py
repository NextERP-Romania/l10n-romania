# Copyright (C) 2026 NextERP Romania
# Copyright (C) 2026 Dakai Soft SRL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import defaultdict

from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _accumulate_amounts(self, data):
        """Stop the closing entry from discharging the stock a second time.

        Point of sale posts the cost of what it sold in the session closing
        entry, gathered from the stock moves of the pickings. The Romanian
        stock accounting posts that same discharge on each move as it is done,
        because `_should_create_account_move` is true for every Romanian
        record. Left alone, closing a session credits 371 and debits 607 twice
        for the same goods, and the shop's stock account drifts by the value of
        everything it sold.

        The three buckets are emptied so the closing entry carries only what
        belongs to it - the takings, the taxes and the receivables - and the
        stock stays where the moves put it.
        """
        data = super()._accumulate_amounts(data)
        if not self.company_id.l10n_ro_accounting:
            return data

        def amounts():
            return {"amount": 0.0, "amount_converted": 0.0}

        data.update(
            {
                "stock_expense": defaultdict(amounts),
                "stock_return": defaultdict(amounts),
                "stock_valuation": defaultdict(amounts),
            }
        )
        return data
