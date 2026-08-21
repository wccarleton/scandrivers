# KT20 driver reference

## Overview

The KT20 driver loads magnetic susceptibility scan exports produced by the KT20 scanner into a tidy pandas DataFrame.

## Supported data files

The driver expects scan files matching patterns such as:

- record_scanner_10khz_*.csv

## Expected input structure

The KT20 CSV format contains:

1. A metadata row with columns such as `Record_ID`, `Date`, `Time`, `Frequency`, `Pin`, and `Diameter corr.`.
2. A subsequent section containing susceptibility measurements.
3. Summary rows for `Kappa` and `Sigma` values.

## Driver expectations

The driver preserves the following metadata columns when present:

- record_id
- date
- time
- frequency
- pin
- diameter_correction
- measurement_type
- density
- picture
- voice_note
- latitude
- longitude
- altitude
- text_note

The main measurement columns produced by the loader are:

- measurement_index
- susceptibility_10_3si
- trigger_data

## Example data

Example sample data for testing lives in:

- src/scandrivers/demo_data/kt20/kt20_0467

The published [KT20 device page](../../../devices/kt20.qmd) is the maintained user-facing reference.
