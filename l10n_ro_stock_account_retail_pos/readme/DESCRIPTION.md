# Romania - Retail Point of Sale (Marfa in Magazin)

Point of sale posts the cost of what a session sold in its closing
entry. The Romanian stock accounting already posts that discharge on
each stock move as it is done. Left alone the two add up: closing a
session credits 371 and debits 607 a second time for the same goods,
and the shop's stock account drifts by the value of everything it sold.

This module empties the stock buckets of the closing entry, so it
carries only what belongs to it - the takings, the taxes and the
receivables - and the stock stays where the moves put it. The markup
and the deferred VAT are released by the moves too, from the markup
ledger, at what the goods were loaded with.

A sale below the shelf price needs no special treatment. 371 is
relieved at the shelf price whatever the till charged, 378 and 4428
close against it, and the discount shows up where it belongs: in the
revenue, and so in the margin. 4428 is a clearing account against 371,
not the VAT payable, so it is not expected to match 4427.

Installs itself as soon as both the retail accounting and the point of
sale are present.
