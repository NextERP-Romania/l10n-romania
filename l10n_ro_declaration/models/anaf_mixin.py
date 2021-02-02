# Copyright (C) 2020 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64

from dateutil.relativedelta import relativedelta
from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import xml_utils

from .column_config import JOURNAL_COLUMNS, SUMED_COLUMNS


class AnafMixin(models.AbstractModel):
    _name = "anaf.mixin"
    _description = "Anaf Declaration Mixin"

    @api.model
    def _get_default_date_from(self):
        today = fields.Date.from_string(fields.Date.today())
        return today + relativedelta(day=1, months=-1)

    @api.model
    def _get_default_date_to(self):
        today = fields.Date.from_string(fields.Date.today())
        return today + relativedelta(day=1, days=-1)

    @api.model
    def _get_default_declaration(self):
        decl = self.env["anaf.declaration"].search([], limit=1)
        return decl

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    declaration_id = fields.Many2one(
        "anaf.declaration", string="ANAF Declaration", default=_get_default_declaration
    )
    version_id = fields.Many2one(
        "anaf.declaration.version",
        string="ANAF Declaration Version",
        domain="[('declaration_id', '=', declaration_id)]",
    )
    signature_id = fields.Many2one(
        "anaf.signature", string="SSL Signature", help="SSL Signature of the Document"
    )
    bank_account_id = fields.Many2one("res.partner.bank", string="Bank Account")

    date_range_id = fields.Many2one(
        comodel_name="date.range",
        string="Date range",
        domain="['|',('company_id','=',company_id)," "('company_id','=',False)]",
    )
    date_from = fields.Date("Start Date", required=True, default=_get_default_date_from)
    date_to = fields.Date("End Date", required=True, default=_get_default_date_to)
    date_next = fields.Date("Next Date", compute="_compute_next_date")
    name = fields.Char("File Name", compute="_compute_anaf_filename", default="")
    file_save = fields.Binary(string="Report File", readonly=True)

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for fy in self:
            # Starting date must be prior to the ending date
            date_from = fy.date_from
            date_to = fy.date_to
            if date_to < date_from:
                raise ValidationError(
                    _("The ending date must not be prior to the starting " "date.")
                )

    @api.onchange("declaration_id")
    def onchange_declaration_id(self):
        if self.declaration_id:
            self.version_id = self.declaration_id.version_ids[0]
        else:
            self.version_id = False

    @api.onchange("date_range_id")
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    @api.model
    def get_months_number(self):
        r = relativedelta(self.date_to, self.date_from)
        months = r.months + 12 * r.years + 1
        return months

    @api.model
    def get_year_month(self):
        year = month = ""
        if self.date_to:
            year = fields.Date.from_string(self.date_to).year
            month = fields.Date.from_string(self.date_to).month
            month = "{:2s}".format(str(month).zfill(2))
        return year, month

    def _compute_next_date(self):
        for record in self:
            months = record.get_months_number()
            if record.date_to:
                record.date_next = self.date_to + relativedelta(day=25, months=months)

    @api.depends("declaration_id", "company_id")
    def _compute_anaf_filename(self):
        year, month = self.get_year_month()
        self.name = "{} - {} - {}-{}.{}".format(
            self.declaration_id.name, self.company_id.vat, year, month, "xml"
        )

    def get_report(self):
        model = self.version_id.model
        validator = self.version_id.validator
        declaration = self.env[model.model].create(
            {
                "company_id": self.company_id.id,
                "bank_account_id": self.bank_account_id.id,
                "signature_id": self.signature_id.id,
                "date_from": self.date_from,
                "date_to": self.date_to,
            }
        )
        xmlfile = declaration.build_file().encode("utf-8")
        parser = etree.XMLParser(ns_clean=True, recover=True, encoding="utf-8")
        h = etree.fromstring(xmlfile, parser=parser)
        if validator:
            xml_utils._check_with_xsd(h, validator.name, self.env)
        self.file_save = base64.encodebytes(xmlfile)
        return {
            "name": _("Save"),
            "context": self.env.context,
            "view_type": "form",
            "view_mode": "form",
            "res_model": self._name,
            "type": "ir.actions.act_window",
            "target": "new",
            "res_id": self.id,
        }

    def value_to_string(self, value):
        return '"' + str(value) + '"'

    @api.model
    def get_period_invoices_by_tags(self, types, tags):
        invoices = (
            self.env["account.move.line"]
            .search(
                [
                    ("move_id.state", "=", "posted"),
                    ("move_id.move_type", "in", types),
                    ("move_id.invoice_date", ">=", self.date_from),
                    ("move_id.invoice_date", "<=", self.date_to),
                    ("tax_tag_ids", "in", tags),
                    "|",
                    ("company_id", "=", self.company_id.id),
                    ("company_id", "in", self.company_id.child_ids.ids),
                ],
            )
            .mapped("move_id")
        )
        return invoices.sorted(key=lambda r: r.invoice_date)

    @api.model
    def get_period_invoices(self, types=False, cancel=False):
        if not types:
            types = [
                "out_invoice",
                "out_refund",
                "in_invoice",
                "in_refund",
                "out_receipt",
                "in_receipt",
            ]

        domain = [
            ("move_type", "in", types),
            ("invoice_date", ">=", self.date_from),
            ("invoice_date", "<=", self.date_to),
            "|",
            ("company_id", "=", self.company_id.id),
            ("company_id", "in", self.company_id.child_ids.ids),
        ]
        if cancel:
            domain = [("state", "in", ("posted", "cancel"))] + domain
        else:
            domain = [("state", "=", "posted")] + domain
        invoices = self.env["account.move"].search(
            domain,
            order="invoice_date, name, ref",
        )
        return invoices

    @api.model
    def get_period_vatp_invoices(self, types):
        fp = self.company_id.property_vat_on_payment_position_id
        if not fp:
            fp = self.env["account.fiscal.position"].search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("name", "=", "Regim TVA la Incasare"),
                ]
            )
        invoices = self.env["account.move"]
        if fp:
            vatp_invoices = self.env["account.move"].search(
                [
                    ("state", "in", ["posted", "cancel"]),
                    ("move_type", "in", types),
                    ("invoice_date", ">", self.company_id.account_opening_date),
                    ("invoice_date", "<=", self.date_to),
                    ("fiscal_position_id", "=", fp.id),
                    "|",
                    ("company_id", "=", self.company_id.id),
                    ("company_id", "in", self.company_id.child_ids.ids),
                ]
            )
            for inv in vatp_invoices:
                if inv.payment_state not in ["paid", "reversed", "invoicing_legacy"]:
                    invoices |= inv
                elif inv.payment_state == "paid":
                    for payment in self._get_reconciled_invoices_partials():
                        if (
                            payment.date >= self.date_from
                            and payment.date <= self.date_to
                        ):
                            invoices |= inv
        return invoices

    @api.model
    def _get_tax_report_domain(self, company_id, date_from, date_to):
        domain = [
            ("company_id", "=", company_id),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
            ("tax_exigible", "=", True),
            ("tax_tag_ids", "!=", False),
            ("move_id.state", "=", "posted"),
        ]
        if self.env.context.get("move_ids", False):
            domain += [("move_id.id", "in", self.env.context["move_ids"])]
        return domain

    def _get_anaf_vat_report_data(self, company_id, date_from, date_to):
        mv_line_obj = self.env["account.move.line"]
        vat_report = {}
        tax_domain = self._get_tax_report_domain(company_id, date_from, date_to)
        tax_move_lines = mv_line_obj.search(tax_domain)
        for record in tax_move_lines:
            for tag in record.tax_tag_ids:
                if record.move_id.tax_cash_basis_rec_id:
                    # Cash basis entries are always treated as misc operations,
                    # applying the tag sign directly to the balance
                    type_multiplicator = -1
                else:
                    type_multiplicator = (
                        record.journal_id.type == "sale" and -1 or 1
                    ) * (
                        mv_line_obj._get_refund_tax_audit_condition(record) and -1 or 1
                    )

                tag_amount = type_multiplicator * record.balance
                if tag.tax_report_line_ids:
                    # Then, the tag comes from a report line, and hence has
                    # a + or - sign (also in its name)
                    for report_line in tag.tax_report_line_ids:
                        tag_id = report_line.tag_name
                        if tag_id not in vat_report.keys():
                            vat_report[tag_id] = 0.0
                        vat_report[tag_id] += tag_amount
                else:
                    # Then, it's a financial tag (sign is always +,
                    # and never shown in tag name)
                    tag_id = tag.name
                    if tag_id not in vat_report.keys():
                        vat_report[tag_id] = 0.0
                    vat_report[tag_id] += tag_amount
        return vat_report

    def get_journal_columns(self):
        return JOURNAL_COLUMNS

    def get_sumed_columns(self):
        return SUMED_COLUMNS

    def get_all_tags(self):
        all_known_tags = {}
        vatp_tags = ["tva_neex", "base_exig", "base_neex", "tva_exig"]
        for k, v in JOURNAL_COLUMNS.items():
            if k not in vatp_tags:
                for tag in v["tags"]:
                    if tag in all_known_tags.keys():
                        all_known_tags[tag] += [k]
                    else:
                        all_known_tags[tag] = [k]
        return all_known_tags

    def get_vatp_not_eligible(self, move, vals, sign):
        nd_tax_base = JOURNAL_COLUMNS["base_neex"]["tags"]
        nd_tax_vat = JOURNAL_COLUMNS["tva_neex"]["tags"]
        for line in move.line_ids:
            for tag in line.tax_tag_ids:
                type_multiplicator = line.journal_id.type == "sale" and 1 or -1
                tag_amount = type_multiplicator * line.balance
                if tag.tax_report_line_ids:
                    # Then, the tag comes from a report line, and hence has a + or - sign (also in its name)
                    for report_line in tag.tax_report_line_ids:
                        tag_id = report_line.tag_name
                        if tag_id in nd_tax_base:
                            vals["base_neex"] += sign * tag_amount
                        elif tag_id in nd_tax_vat:
                            vals["tva_neex"] += sign * tag_amount
                else:
                    # Then, it's a financial tag (sign is always +, and never shown in tag name)
                    tag_id = tag.name
                    if tag_id in nd_tax_base:
                        vals["base_neex"] += sign * tag_amount
                    elif tag_id in nd_tax_vat:
                        vals["tva_neex"] += sign * tag_amount
        return vals

    def get_payment_vals(self, vals, sign, invoice):
        # This invoice is vat on payment and we are going to put the payments
        # search the reconcile line
        all_known_tags = self.get_all_tags()
        for line in invoice.line_ids:
            if line.account_id.code.startswith(
                "411"
            ) or line.account_id.code.startswith("401"):
                break

        vatp_tags = JOURNAL_COLUMNS["base_neex"]["tags"]
        res = self.with_context(move_ids=invoice.ids)._get_anaf_vat_report_data(
            self.company_id.id, invoice.invoice_date, invoice.invoice_date
        )
        if res:
            for _key, value in res.items():
                if _key in vatp_tags:
                    vals["base_neex"] += value
        # find all the reconciliation till date to
        partial_rec = invoice.mapped("line_ids.matched_debit_ids") + invoice.mapped(
            "line_ids.matched_credit_ids"
        )

        for partial in partial_rec:
            moves = partial.mapped("debit_move_id") + partial.mapped("credit_move_id")
            partials = (
                moves.filtered(lambda m: m.date <= self.date_to).mapped("move_id")
                - invoice
            )
            for payment in partials:
                moves = self.env["account.move"].search(
                    [("tax_cash_basis_rec_id", "=", partial.id)]
                )
                for move in moves:
                    if move.date <= self.date_to:
                        vals = self.get_vatp_not_eligible(move, vals, sign)
                    if move.date >= self.date_from:
                        # is payment in period and we are going also
                        # to show it, and also substract it
                        vals["rowspan"] += 1
                        payment = {
                            "number": move.ref,
                            "date": move.date,
                            "amount": payment.amount_total,
                            "base_19": 0,
                            "base_9": 0,
                            "base_5": 0,
                            "tva_19": 0,
                            "tva_9": 0,
                            "tva_5": 0,
                        }
                        res = self.with_context(
                            move_ids=move.ids
                        )._get_anaf_vat_report_data(
                            self.company_id.id, self.date_from, self.date_to
                        )
                        if res:
                            for _key, value in res.items():
                                if _key in all_known_tags.keys():
                                    for tagx in all_known_tags[_key]:
                                        if tagx in payment:
                                            payment[tagx] += sign * value
                        vals["payments"].append(payment)
        if vals.get("base_neex"):
            vals["base_neex"] = round(
                sign * invoice.amount_untaxed_signed - vals.get("base_neex"), 2
            )
        if vals.get("tva_neex"):
            vals["tva_neex"] = round(
                sign * invoice.amount_tax_signed - vals.get("tva_neex"), 2
            )
        return vals

    def get_journal_line_vals(self, invoice, vals=False, journal_type=True, sign=1):
        # l10n_ro_declaration / models / anaf_mixin.py: 376:5: C901
        # 'AnafMixin.get_journal_line_vals' is too
        # complex(17)
        if not vals:
            journal_columns = self.get_journal_columns()
            sumed_colums = self.get_sumed_columns()
            vals = self.add_new_row(journal_columns, sumed_colums)
        all_known_tags = self.get_all_tags()
        (
            country_code,
            identifier_type,
            vat_number,
        ) = invoice.commercial_partner_id._parse_anaf_vat_info()
        new_sign = sign
        if journal_type and invoice.move_type in [
            "in_invoice",
            "out_refund",
            "in_receipt",
        ]:
            new_sign = -1 * sign

        vals["number"] = invoice.name
        vals["date"] = invoice.invoice_date
        vals["partner"] = invoice.commercial_partner_id.name
        vals["vat"] = invoice.invoice_partner_display_vat
        vals["total"] = new_sign * (invoice.amount_total_signed)
        vals["warnings"] = ""
        vals["rowspan"] = 1

        put_payments = False
        # after parsing the invoice lines, if is vat on payment,
        # to put also the payments take all the lines from this
        # invoice and put them into dictionary
        res = self.with_context(move_ids=invoice.ids)._get_anaf_vat_report_data(
            self.company_id.id, self.date_from, self.date_to
        )
        if res:
            for _key, value in res.items():
                if _key in all_known_tags.keys():
                    for tagx in all_known_tags[_key]:
                        vals[tagx] += value
        for line in invoice.line_ids:
            if line.tax_tag_ids and not line.tax_exigible:  # VAT on payment
                put_payments = True

        if put_payments:
            vals = self.get_payment_vals(vals, new_sign, invoice)

        if vals["rowspan"] > 1:
            vals["rowspan"] -= 1

        if put_payments and vals.get("payments"):
            for pay in vals.get("payments"):
                for _key, value in SUMED_COLUMNS.items():
                    for tag in value:
                        vals[tag] += pay.get(tag, 0)
                pay["base_exig"] = pay["base_19"] + pay["base_9"] + pay["base_5"]
                pay["tva_exig"] = pay["tva_19"] + pay["tva_9"] + pay["tva_5"]
        for _key, value in SUMED_COLUMNS.items():
            # put the aggregated values ( summed columns)
            vals[_key] = sum([vals[x] for x in value])
        if identifier_type == "1":
            vals["base_ded1"] = 0.0
            vals["scutit1"] = 0.0
        else:
            vals["base_0"] = 0.0
        return vals

    def add_new_row(self, journal_columns, sumed_colums):
        empty_row = {k: 0.0 for k in sumed_colums}
        empty_row.update(
            {k: 0.0 for k, v in journal_columns.items() if v["type"] == "int"}
        )
        empty_row.update(
            {k: "" for k, v in journal_columns.items() if v["type"] == "char"}
        )
        empty_row.update(
            {k: [] for k, v in journal_columns.items() if v["type"] == "list"}
        )
        return empty_row

    def get_cota_vals(self, invoice, journal_type=True, sign=1):
        def _update_cotas(line, cotas, tax_ids, new_sign, anaf_code=False):
            if not anaf_code:
                anaf_code = ""
            for tax in tax_ids:
                cota = int(tax.mapped("amount")[0])
                res = tax.compute_all(line.balance)
                amount = sum(tax.get("amount", 0.0) for tax in res["taxes"])
                cota_line = list(
                    filter(
                        lambda r: r["cota"] == cota and r["anaf_code"] == anaf_code,
                        cotas,
                    )
                )
                if cota_line:
                    cota_line[0]["base"] += new_sign * line.balance
                    cota_line[0]["vat"] += new_sign * amount
                else:
                    cotas.append(
                        {
                            "cota": cota,
                            "nr_fact": 1,
                            "base": new_sign * line.balance,
                            "vat": new_sign * amount,
                            "anaf_code": anaf_code,
                        }
                    )
            return cotas

        new_sign = sign
        if journal_type and invoice.move_type in [
            "out_invoice",
            "out_receipt",
            "in_refund",
        ]:
            new_sign = -1 * sign
        cotas = []
        for line in invoice.invoice_line_ids:
            anaf_code = line.product_id.anaf_code_id.name
            if new_sign > 0:
                tax_ids = line.tax_ids.filtered(
                    lambda tax: tax.amount_type == "percent"
                )
                cotas = _update_cotas(line, cotas, tax_ids, new_sign, anaf_code)
            else:
                if invoice.operation_type in ["V", "C"]:
                    tax_ids = line.product_id.supplier_taxes_id.filtered(
                        lambda tax: tax.amount_type == "percent"
                    )
                else:
                    tax_ids = line.tax_ids.filtered(
                        lambda tax: tax.amount_type == "percent"
                    )
                cotas = _update_cotas(line, cotas, tax_ids, new_sign, anaf_code)
        return cotas
