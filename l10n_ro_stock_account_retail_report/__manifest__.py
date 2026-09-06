# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Romania - Retail Stock Report (Marfa in Magazin)",
    "version": "19.0.1.0.0",
    "category": "Localization",
    "countries": ["ro"],
    "summary": "Romania - Retail stock report (adaos si TVA neexigibila "
    "pe stocul din magazin)",
    "author": "NextERP Romania,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-romania",
    "depends": [
        "l10n_ro_stock_account_retail",
        "l10n_ro_stock_report",
    ],
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "report/stock_retail_report_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "development_status": "Beta",
    "maintainers": ["feketemihai"],
}
