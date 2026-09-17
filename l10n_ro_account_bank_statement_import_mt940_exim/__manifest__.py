# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "MT940 EXIM Format Bank Statements Import",
    "version": "20.0.0.3.0",
    "license": "AGPL-3",
    "summary": "Romania - Import bank statements from Eximbank",
    "author": "NextERP Romania SRL, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-romania",
    "category": "Localization",
    "depends": ["l10n_ro_account_bank_statement_import_mt940_base"],
    # Not installable on 20.0: depends on account_statement_import_file (OCA), which has no Odoo 20
    # counterpart yet. Flip back once it is available.
    "installable": False,
    "development_status": "Beta",
    "maintainers": ["feketemihai"],
}
