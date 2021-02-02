# Copyright (C) 2020 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Romania - Account Report Journal",
    "summary": "Romania - Account Report Journal",
    "version": "14.0.1.0.0",
    "development_status": "Mature",
    "category": "Localization",
    "website": "https://github.com/OCA/l10n-romania",
    "author": "NextERP Romania," "Odoo Community Association (OCA)",
    "maintainers": ["feketemihai"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["l10n_ro_declaration"],
    "data": [
        "report/report_sale_purchase_layout.xml",
        "report/report_sale_journal_layout.xml",
        "report/report_purchase_journal_layout.xml",
        "report/report_sale_purchase_journal.xml",
        "wizard/select_report_sale_purchase_view.xml",
        "security/ir.model.access.csv",
    ],
}
