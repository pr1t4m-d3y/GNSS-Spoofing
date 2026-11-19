# Data

`train.xls` is a legacy Excel sheet of receiver telemetry (16 columns: `time`, `channel`, `PRN`, `Carrier_Doppler_hz`, `Pseudorange_m`, `RX_time`, `TOW`, `Carrier_phase`, `EC`, `LC`, `PC`, `PIP`, `PQP`, `TCD`, `CN0`, `spoofed`). It needs `xlrd` to read; `python -m gnss_shield.train` and `evals/run.py` load it through `gnss_shield.data.load_training_sheet`.

Measured with `docs/audit/a1_data_facts.py` and `docs/audit/a2_eval_probe.py` (see `docs/audit/output/`):

* 65,535 raw rows (the row limit of the `.xls` format), 8 placeholder rows and about 40,800 rows without satellite lock (`PRN = 0`) are discarded, leaving 24,725 usable rows.
* 8 channels (`ch0` to `ch7`) and 7 distinct PRNs.
* The `spoofed` column is 0 for every usable row: the sheet contains genuine signals only.

## Source and credit

The schema matches the public dataset by Ghilas Aissou (University of North Dakota), *A DATASET for GPS Spoofing Detection on Unmanned Aerial System*, Mendeley Data V3, 2022, DOI [10.17632/z7dj3yyzt8.3](https://doi.org/10.17632/z7dj3yyzt8.3), licence CC BY 4.0 (read from its Mendeley page). The sheet in this repository was handed out for a college hackathon at SRM; whether it is a verbatim subset of that dataset has not been confirmed (see [../docs/ROADMAP.md](../docs/ROADMAP.md)). Anyone reusing the data should cite the original dataset.

The hackathon's separate unlabelled `test.xls` is not included.
