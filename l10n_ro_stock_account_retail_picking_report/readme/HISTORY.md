## 19.0.1.1.0 (2026-11-07)

- On a retail reception the plain valued money columns (unit price, additional charges, subtotal, taxes, total) are now hidden, so only the retail columns (purchase price and value, markup, shelf price with and without VAT, deferred VAT) print. The table no longer grows to a dozen-odd columns half of which are zero.
- The retail aggregation now skips packed lines when the slip asks for the unpackaged section, so a packed line is no longer charged onto the unpackaged row that shares its key.
