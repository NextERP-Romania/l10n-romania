# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    # Extend the existing landed-cost type so the goods receipt note can break
    # the additional costs down into transport and excise (next to the types
    # other modules already add: dvi, price_diff). The excise amount the NIR
    # prints comes only from a landed cost of this type - never recomputed from
    # the product excise category.
    l10n_ro_cost_type = fields.Selection(
        selection_add=[("transport", "Transport"), ("excise", "Excise")],
        ondelete={"transport": "set default", "excise": "set default"},
    )
