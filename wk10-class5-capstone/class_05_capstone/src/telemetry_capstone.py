import csv
import os
import sys
from collections import defaultdict

def convert_pressure(value, unit):
    """Return pressure in kPa. 1 psi = 6.8947572932 kPa."""
    if unit == "kPa":
        return value
    if unit == "psi":
        return value * 6.8947572932
    raise ValueError(f"Unsupported pressure unit: {unit}")

def convert_temperature(value, unit):
    """Return temperature in degrees Celsius."""
    if unit == "C":
        return value
    if unit == "F":
        return (value - 32) * 5 / 9
    raise ValueError(f"Unsupported temperature unit: {unit}")

def parse_record(raw_line):
    """Return normalized dictionary; raise ValueError for malformed records."""
    parts = [p.strip() for p in raw_line.strip().split("|")]
    if len(parts) != 7:
        raise ValueError(f"Expected 7 fields, got {len(parts)}")

    timestamp, well_id, pressure_raw, pressure_unit, temp_raw, temp_unit, status = parts

    if not timestamp or not well_id:
        raise ValueError("Missing timestamp or well_id")

    if status not in ("ACTIVE", "INACTIVE"):
        raise ValueError(f"Invalid status: {status}")

    try:
        pressure_value = float(pressure_raw)
    except ValueError:
        raise ValueError(f"Invalid pressure value: {pressure_raw}")

    if pressure_value < 0:
        raise ValueError(f"Negative pressure value: {pressure_raw}")

    try:
        temp_value = float(temp_raw)
    except ValueError:
        raise ValueError(f"Invalid temperature value: {temp_raw}")

    pressure_kpa = round(convert_pressure(pressure_value, pressure_unit), 2)
    temperature_c = round(convert_temperature(temp_value, temp_unit), 2)

    return {
        "timestamp": timestamp,
        "well_id": well_id,
        "pressure_kpa": pressure_kpa,
        "temperature_c": temperature_c,
        "status": status,
    }

def process_lines(lines):
    """Return (accepted_records, rejected_records) preserving source line numbers."""
    accepted = []
    rejected = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = parse_record(line)
            record["line_number"] = line_number
            accepted.append(record)
        except ValueError as e:
            rejected.append({
                "line_number": line_number,
                "reason": str(e),
                "raw_record": line.strip(),
            })
    return accepted, rejected

def summarize_by_well(records):
    """Average pressure in kPa for ACTIVE records, sorted by well ID."""
    totals = defaultdict(list)
    for r in records:
        if r["status"] == "ACTIVE":
            totals[r["well_id"]].append(r["pressure_kpa"])

    summary = []
    for well_id in sorted(totals):
        values = totals[well_id]
        summary.append({
            "well_id": well_id,
            "active_readings": len(values),
            "avg_pressure_kpa": round(sum(values) / len(values), 2),
        })
    return summary

def write_csv(path, fieldnames, records):
    """Create output CSV with a header row."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({k: r.get(k, "") for k in fieldnames})

def run(input_path, output_dir):
    """Generate cleaned_telemetry.csv, rejected_records.csv, well_summary.csv."""
    os.makedirs(output_dir, exist_ok=True)
    with open(input_path, encoding="utf-8") as f:
        lines = f.readlines()

    accepted, rejected = process_lines(lines)
    summary = summarize_by_well(accepted)

    write_csv(
        os.path.join(output_dir, "cleaned_telemetry.csv"),
        ["timestamp", "well_id", "pressure_kpa", "temperature_c", "status"],
        accepted,
    )
    write_csv(
        os.path.join(output_dir, "rejected_records.csv"),
        ["line_number", "reason", "raw_record"],
        rejected,
    )
    write_csv(
        os.path.join(output_dir, "well_summary.csv"),
        ["well_id", "active_readings", "avg_pressure_kpa"],
        summary,
    )
    return accepted, rejected, summary

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python telemetry_capstone.py INPUT_FILE OUTPUT_FOLDER")
        sys.exit(1)
    accepted, rejected, summary = run(sys.argv[1], sys.argv[2])
    print("Done! Accepted:", len(accepted), "Rejected:", len(rejected), "Wells:", len(summary))
    print("Files written to", sys.argv[2])