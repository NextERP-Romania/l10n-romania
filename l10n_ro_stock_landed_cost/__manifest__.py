# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

{
    "name": "Stock Landed Cost",
    "version": "14.0.2.0.0",
    "depends": [
        "stock_landed_costs",
        "l10n_ro_stock_account",
        # to function only if company_id.l10n_ro_accounting
        # to have only stock_account in product category
    ],
    "description": """Stock Landed Cost""",
    "data": [],
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "support": "contact@nexterp.ro",
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "license": "OPL-1",
}
