# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class StockRetailReport(models.Model):
    """What each shop carries on 371, and whether the shelf price still agrees.

    One row per (warehouse, product). The markup and the deferred VAT come from
    the markup ledger, so they are the amounts actually sitting on 378 and 4428
    - not a recomputation from today's pricelist, which is what the report used
    to do and which quietly hid every product whose price had moved since it
    was received.

    The gap between the retail value carried and the current shelf price is
    published as its own column: it is the amount a price change document still
    has to settle, and the reason it exists.
    """

    _name = "l10n.ro.stock.retail.report"
    _description = "Retail stock report (Marfa in magazin)"
    _auto = False
    _order = "warehouse_id, product_id"

    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", readonly=True)
    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    product_tmpl_id = fields.Many2one(
        "product.template", string="Product Template", readonly=True
    )
    categ_id = fields.Many2one("product.category", string="Category", readonly=True)
    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", readonly=True
    )

    quantity = fields.Float(string="Quantity On Hand", readonly=True)
    markup_total = fields.Monetary(
        string="Markup Carried (378)",
        readonly=True,
        currency_field="currency_id",
    )
    vat_total = fields.Monetary(
        string="Deferred VAT Carried (4428)",
        readonly=True,
        currency_field="currency_id",
    )

    cost_total = fields.Monetary(
        string="Stock Value (cost)",
        compute="_compute_values",
        currency_field="currency_id",
    )
    cost_unit = fields.Monetary(
        string="Cost / Unit", compute="_compute_values", currency_field="currency_id"
    )
    retail_value = fields.Monetary(
        string="Retail Value (371)",
        compute="_compute_values",
        currency_field="currency_id",
        help="Cost plus the markup and deferred VAT carried - what account 371 "
        "holds for this stock.",
    )
    retail_price_unit = fields.Monetary(
        string="Carried PVA / Unit",
        compute="_compute_values",
        currency_field="currency_id",
        help="Retail value per unit, VAT included, as loaded.",
    )
    current_price_unit = fields.Monetary(
        string="Current Shelf Price / Unit",
        compute="_compute_values",
        currency_field="currency_id",
        help="Shelf price the warehouse pricelist gives today, VAT included.",
    )
    price_gap_total = fields.Monetary(
        string="To Revalue",
        compute="_compute_values",
        currency_field="currency_id",
        help="Difference between the current shelf price and what the stock "
        "carries. Anything other than zero means a price change document is "
        "due for this product.",
    )

    @property
    def _table_query(self):
        return """
            SELECT
                MIN(ml.id) AS id,
                ml.company_id AS company_id,
                ml.warehouse_id AS warehouse_id,
                ml.product_id AS product_id,
                pp.product_tmpl_id AS product_tmpl_id,
                pt.categ_id AS categ_id,
                SUM(ml.quantity)::numeric AS quantity,
                SUM(ml.markup)::numeric AS markup_total,
                SUM(ml.vat)::numeric AS vat_total
            FROM l10n_ro_retail_markup_line ml
            JOIN product_product pp ON pp.id = ml.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE ml.warehouse_id IS NOT NULL
            GROUP BY ml.company_id, ml.warehouse_id, ml.product_id,
                     pp.product_tmpl_id, pt.categ_id
            HAVING SUM(ml.quantity) > 0
        """

    @api.depends("product_id", "warehouse_id", "quantity", "markup_total", "vat_total")
    def _compute_values(self):
        cost_by_key = self._l10n_ro_cost_on_hand()
        for rec in self:
            company = rec.company_id or self.env.company
            currency = company.currency_id
            qty = rec.quantity or 0.0
            cost_total = cost_by_key.get((rec.warehouse_id.id, rec.product_id.id), 0.0)
            retail_value = cost_total + rec.markup_total + rec.vat_total
            rec.cost_total = currency.round(cost_total)
            rec.cost_unit = currency.round(cost_total / qty) if qty else 0.0
            rec.retail_value = currency.round(retail_value)
            rec.retail_price_unit = currency.round(retail_value / qty) if qty else 0.0
            current_unit = (
                rec.product_id._l10n_ro_get_retail_price(
                    warehouse=rec.warehouse_id, company=company
                )
                if rec.product_id and rec.warehouse_id
                else 0.0
            )
            rec.current_price_unit = currency.round(current_unit)
            rec.price_gap_total = currency.round(current_unit * qty - retail_value)

    def _l10n_ro_cost_on_hand(self):
        """Cost of the stock on hand per (warehouse, product), in one pass.

        ``stock.quant.value`` is computed, so it cannot be joined in the view;
        reading it row by row would be one query per product.
        """
        if not self:
            return {}
        quants = (
            self.env["stock.quant"]
            .sudo()
            .search(
                [
                    ("product_id", "in", self.product_id.ids),
                    ("location_id.warehouse_id", "in", self.warehouse_id.ids),
                    ("location_id.l10n_ro_retail", "=", True),
                ]
            )
        )
        result = {}
        for quant in quants:
            key = (quant.location_id.warehouse_id.id, quant.product_id.id)
            result[key] = result.get(key, 0.0) + quant.value
        return result
