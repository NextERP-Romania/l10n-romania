# Copyright (C) 2020 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from copy import deepcopy

from odoo import api, fields, models


class SaleJournalReport(models.TransientModel):
    _name = "report.l10n_ro_account_report_journal.report_sp"
    _description = "Report Sale Purchase Journal"

    @api.model
    def _get_report_values(self, docids=None, data=None):
        journal_type = data["journal_type"]
        anaf = self.env["l10n.ro.account.report.journal"].browse(data["id"])
        if anaf.date_range_id:
            anaf.write(
                {
                    "date_from": anaf.date_range_id.date_start,
                    "date_to": anaf.date_range_id.date_end,
                }
            )
        if journal_type == "sale":
            types = ["out_invoice", "out_refund", "out_receipt"]
        else:
            types = ["in_invoice", "in_refund", "in_receipt"]
        invoices = anaf.get_period_invoices(types)
        invoices |= anaf.get_period_vatp_invoices(types)
        invoices = invoices.sorted(key=lambda r: r.invoice_date or r.date)
        if journal_type == "sale":
            types = ["in_invoice", "in_refund", "in_receipt"]
            supp_tags_name = [
                "05 - BAZA",
                "05 - TVA",
                "07 - BAZA",
                "07 - TVA",
                "12_1 - BAZA",
                "12_1 - TVA",
                "12_2 - BAZA",
                "12_2 - TVA",
                "12_3 - BAZA",
                "12_3 - TVA",
            ]
            tags_obj = self.env["account.account.tag"]
            tags = self.env["account.account.tag"]
            for tag in supp_tags_name:
                tags |= tags_obj._get_tax_tags(tag, anaf.company_id.country_id.id)
            supp_invoices = anaf.get_period_invoices_by_tags(types, tags.ids)
            invoices |= supp_invoices
        show_warnings = data["show_warnings"]
        report_type_sale = journal_type == "sale"
        report_lines, totals = self.compute_report_lines(
            anaf, invoices, report_type_sale
        )

        docargs = {
            "print_datetime": fields.datetime.now(),
            "date_from": anaf.date_from,
            "date_to": anaf.date_to,
            "show_warnings": show_warnings,
            "user": self.env.user.name,
            "company": anaf.company_id,
            "lines": report_lines,
            "totals": totals,
            "report_type_sale": report_type_sale,
        }
        return docargs

    def compute_report_lines(self, anaf, invoices, report_type_sale=True):
        """input:
        invoices = account.move list of invoices to be showed in report
        payments = account.move list of payments done on vat_on_payment invoices
        vat_on_payment_reconcile = partial.reconcile  list of efective accounting
                                   moves that are telling what taxes are to be paid
        returns a list of a dictionary for table with the key as column
        and total dictionary with the sums of columns"""

        if not invoices:
            return [], {}
        # must be int
        journal_columns = anaf.get_journal_columns()
        sumed_colums = anaf.get_sumed_columns()
        empty_row = anaf.add_new_row(journal_columns, sumed_colums)
        sign = 1 if report_type_sale else -1
        report_lines = []

        for inv1 in invoices:
            vals = deepcopy(empty_row)
            vals = anaf.get_journal_line_vals(inv1, vals, report_type_sale, sign)
            report_lines += [vals]  # we added another line to the table

        # make the totals dictionary for total line of table as sum of all the integer/float values of vals
        int_float_keys = []
        for key, value in report_lines[0].items():
            if (type(value) is int) or (type(value) is float):
                int_float_keys.append(key)
        totals = {}
        for key in int_float_keys:
            totals[key] = round(sum([x[key] for x in report_lines]), 2)
        totals["payments"] = []
        return report_lines, totals
