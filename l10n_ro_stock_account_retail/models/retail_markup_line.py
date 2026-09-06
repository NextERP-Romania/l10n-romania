# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class RetailMarkupLine(models.Model):
    """Subsidiary ledger for the retail markup (378) and deferred VAT (4428).

    Odoo 19 dropped ``stock.valuation.layer``: the value of a move lives on
    ``stock.move.value`` and carries the cost only. The markup and the deferred
    VAT that make up the difference between cost and shelf price (PVA) have
    nowhere to live, so without a record of them the only way to release them
    when the goods leave the shop is to recompute from the *current* pricelist.
    That is wrong whenever the price moved between entry and exit: the release
    does not match what was loaded, and 371 drifts away from the stock.

    Every event that changes the markup carried on 371 writes one row here:
    a stock move crossing the retail boundary, a posted price change, a landed
    cost, a purchase price difference. The balance of the rows for a given
    (warehouse, product) is what is actually sitting on 378 and 4428, so a
    release is always taken from what was loaded, and the last unit out closes
    both accounts to zero.

    This is the *coeficient de repartizare a adaosului comercial* of the
    Romanian retail monograph, applied per movement instead of per month.
    """

    _name = "l10n.ro.retail.markup.line"
    _description = "Retail Markup Ledger Line (Adaos si TVA neexigibila)"
    _order = "date desc, id desc"

    company_id = fields.Many2one(
        "res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    company_currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", readonly=True
    )
    date = fields.Datetime(required=True, index=True, default=fields.Datetime.now)
    product_id = fields.Many2one(
        "product.product", required=True, index=True, ondelete="restrict"
    )
    location_id = fields.Many2one(
        "stock.location", required=True, index=True, ondelete="restrict"
    )
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        related="location_id.warehouse_id",
        store=True,
        index=True,
        readonly=True,
    )
    quantity = fields.Float(
        digits="Product Unit of Measure",
        help="Signed quantity: positive when goods enter the shop, negative "
        "when they leave. Price changes and cost corrections carry zero.",
    )
    markup = fields.Monetary(
        string="Markup (378)",
        currency_field="company_currency_id",
        help="Signed amount posted to the markup account by this event.",
    )
    vat = fields.Monetary(
        string="Deferred VAT (4428)",
        currency_field="company_currency_id",
        help="Signed amount posted to the deferred VAT account by this event.",
    )
    origin_type = fields.Selection(
        [
            ("move", "Stock Move"),
            ("price_change", "Price Change"),
            ("landed_cost", "Landed Cost"),
            ("price_difference", "Price Difference"),
            ("manual", "Manual"),
        ],
        required=True,
        default="move",
        index=True,
    )
    move_id = fields.Many2one(
        "stock.move", string="Stock Move", index="btree_not_null", ondelete="set null"
    )
    account_move_id = fields.Many2one(
        "account.move", index="btree_not_null", ondelete="set null"
    )
    reference = fields.Char()

    # ------------------------------------------------------------------
    # Balances
    # ------------------------------------------------------------------
    @api.model
    def _l10n_ro_carried(self, warehouse, product, company, exclude=None):
        """Return ``(markup, vat)`` currently carried on the retail stock of
        ``warehouse`` for ``product``.

        ``exclude`` is a ``l10n.ro.retail.markup.line`` recordset to leave out,
        used while a move is being posted so it does not see its own rows.

        The balance is kept per warehouse, not per location: the shelf price
        comes from the warehouse pricelist, so that is the level at which the
        markup is homogeneous. Putaway rules that spread one reception over
        several bins therefore do not fragment it.
        """
        domain = [
            ("company_id", "=", company.id),
            ("product_id", "=", product.id),
            ("warehouse_id", "=", warehouse.id),
        ]
        if exclude:
            domain.append(("id", "not in", exclude.ids))
        groups = self.sudo()._read_group(domain, aggregates=["markup:sum", "vat:sum"])
        markup, vat = groups[0] if groups else (0.0, 0.0)
        return markup or 0.0, vat or 0.0

    @api.model
    def _l10n_ro_carried_qty(self, warehouse, product, company):
        """Quantity of ``product`` on hand in the retail locations of
        ``warehouse``, i.e. the quantity that carries the balance above."""
        groups = (
            self.env["stock.quant"]
            .sudo()
            ._read_group(
                [
                    ("company_id", "=", company.id),
                    ("product_id", "=", product.id),
                    ("location_id.warehouse_id", "=", warehouse.id),
                    ("location_id.l10n_ro_retail", "=", True),
                ],
                aggregates=["quantity:sum"],
            )
        )
        return (groups[0][0] if groups else 0.0) or 0.0
