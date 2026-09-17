# Copyright (C) 2016 Forest and Biomass Romania
# Copyright (C) 2022 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "MT940 Raiffeisen Format Bank Statements Import",
    "category": "Localization",
    "summary": "Romania - Import bank statements from Raiffeisen",
    "depends": ["l10n_ro_account_bank_statement_import_mt940_base"],
    "license": "AGPL-3",
    "version": "20.0.0.3.0",
    "author": "NextERP Romania,"
    "Forest and Biomass Romania,"
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-romania",
    # Not installable on 20.0: depends on account_statement_import_file (OCA), which has no Odoo 20
    # counterpart yet. Flip back once it is available.
    "installable": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai", "dhongu"],
}
