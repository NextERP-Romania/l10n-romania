# Copyright (C) 2013-2015 Therp BV <http://therp.nl>
# Copyright (C) 2022 NextERP Romania
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Romania - MT940 Bank Statements Import",
    "summary": "Romania - MT940 Bank Statements Import",
    "version": "20.0.0.5.0",
    "license": "AGPL-3",
    "author": "NextERP Romania,Odoo Community Association (OCA),Therp BV",
    "website": "https://github.com/OCA/l10n-romania",
    "category": "Localization",
    "depends": ["account_statement_import_file", "l10n_ro_config"],
    "data": ["views/res_bank_view.xml"],
    # Not installable on 20.0: depends on account_statement_import_file (OCA), which has no Odoo 20
    # counterpart yet. Flip back once it is available.
    "installable": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai", "dhongu"],
}
