# Week 10  Class 5 Capstone - Drilling Telemetry Data Processing System

Junior data analyst project. Converts raw drilling telemetry logs into trusted CSV files for engineering review.

## How to run

```bash
python src/telemetry_capstone.py data/drilling_telemetry_capstone.txt outputs

## What it does

- Reads pipe-separated records: `timestamp | well_id | pressure_value | pressure_unit | temperature_value | temperature_unit | status`
- Converts pressure from `psi` to `kPa` using `1 psi = 6.8947572932 kPa`. `kPa` input stays as `kPa`.
- Converts temperature from `F` to `C` using `(F - 32) x 5/9`. `C` input stays as `C`.
- Rejects non-numeric measurements, negative pressures, unsupported units, and any status other than `ACTIVE` or `INACTIVE`.
- Continues after bad records. Tracks original 1-based line numbers and a reason for every rejected record.
- Rounds converted pressure and temperature to 2 decimal places.

## Outputs - in `outputs/` folder

- `cleaned_telemetry.csv` - `timestamp, well_id, pressure_kpa, temperature_c, status`
- `rejected_records.csv` - `line_number, reason, raw_record`
- `well_summary.csv` - `well_id, active_readings, avg_pressure_kpa` - ACTIVE only, sorted by well_id

## Tests

```bash
python -m unittest discover -s tests -v
'''
## Notes
- Python standard library only. No Pandas / NumPy.
- All records are synthetic and for education only. Do not use for operational drilling decisions.