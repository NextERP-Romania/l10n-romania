# Copyright (C) 2020 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

JOURNAL_COLUMNS = {
    "base_col": {
        "type": "int",
        "tags": [
            "05 - BAZA",
            "07 - BAZA",
            "12_1 - BAZA",
            "12_2 - BAZA",
            "12_3 - BAZA",
        ],
    },
    "tva_col": {
        "type": "int",
        "tags": [
            "05 - TVA",
            "07 - TVA",
            "12_1 - TVA",
            "12_2 - TVA",
            "12_3 - TVA",
        ],
    },
    "base_exig": {
        "type": "int",
        "tags": [
            "09 - BAZA",
            "10 - BAZA",
            "11 - BAZA",
            "14 - BAZA",
            "24_1 - BAZA",
            "24_2 - BAZA",
            "25_1 - BAZA",
            "25_2 - BAZA",
            "26_1 - BAZA",
            "26_2 - BAZA",
        ],
    },
    "tva_exig": {
        "type": "int",
        "tags": [
            "09 - TVA",
            "10 - TVA",
            "11 - TVA",
            "24_1 - TVA",
            "24_2 - TVA",
            "25_1 - TVA",
            "25_2 - TVA",
            "26_1 - TVA",
            "26_2 - TVA",
        ],
    },
    "base_19": {
        "type": "int",
        "tags": ["09 - BAZA", "24_1 - BAZA", "24_2 - BAZA"],
    },
    "tva_19": {
        "type": "int",
        "tags": ["09 - TVA", "24_1 - TVA", "24_2 - TVA"],
    },
    "base_9": {
        "type": "int",
        "tags": ["10 - BAZA", "25_1 - BAZA", "25_2 - BAZA"],
    },
    "tva_9": {
        "type": "int",
        "tags": ["10 - TVA", "25_1 - TVA", "25_2 - TVA"],
    },
    "base_5": {
        "type": "int",
        "tags": ["11 - BAZA", "26_1 - BAZA", "26_2 - BAZA"],
    },
    "tva_5": {
        "type": "int",
        "tags": ["11 - TVA", "26_1 - TVA", "26_2 - TVA"],
    },
    "base_0": {"type": "int", "tags": ["14 - BAZA", "30 - BAZA"]},
    "invers": {"type": "int", "tags": ["13 - BAZA"]},
    "payments": {"type": "list", "tags": []},
    "base_neex": {
        "type": "int",
        "tags": [
            "09 - BAZA",
            "10 - BAZA",
            "11 - BAZA",
            "14 - BAZA",
            "24_1 - BAZA",
            "24_2 - BAZA",
            "25_1 - BAZA",
            "25_2 - BAZA",
            "26_1 - BAZA",
            "26_2 - BAZA",
            "30 - BAZA",
        ],
    },
    "tva_neex": {
        "type": "int",
        "tags": [
            "09 - TVA",
            "10 - TVA",
            "11 - TVA",
            "24_1 - TVA",
            "24_2 - TVA",
            "25_1 - TVA",
            "25_2 - TVA",
            "26_1 - TVA",
            "26_2 - TVA",
        ],
    },
    "neimp": {"type": "int", "tags": ["30 - BAZA"]},
    "others": {"type": "int", "tags": ["03_1 - BAZA"]},
    "scutit1": {
        "type": "int",
        "tags": ["01 - BAZA", "30 - BAZA"],
    },  # intracomunitar servicii
    "scutit2": {
        "type": "int",
        "tags": ["03 - BAZA", "30_1 - BAZA"],
    },  # intracomunitar bunuri
    "base_ded1": {
        "type": "int",
        "tags": ["14 - BAZA", "22_1 - BAZA"],
    },  # cu drept de deducere
    "tva_ded1": {"type": "int", "tags": ["22_1 - TVA"]},
    "base_ded2": {
        "type": "int",
        "tags": ["15 - BAZA", "20_1 - BAZA"],
    },  # fara drept de deducere
    "tva_ded2": {"type": "int", "tags": ["20_1 - TVA"]},
    "base_inverse_taxation": {
        "type": "int",
        "tags": ["27_1 - BAZA", "27_2 - BAZA", "27_3 - BAZA"],
    },
    "tva_inverse_taxation": {
        "type": "int",
        "tags": ["27_1 - TVA", "27_2 - TVA", "27_3 - TVA"],
    },
}

SUMED_COLUMNS = {
    "total_base": ["base_19", "base_9", "base_5", "base_0", "base_exig"],
    "total_vat": ["tva_19", "tva_9", "tva_5", "tva_exig"],
}
