import pandas as pd
from typing import Dict, Optional
import math
from pathlib import Path
import config


def load_headcount_data(
    xlsx_path: str,
    *,
    locations_csv: Path = Path(config.MAPPINGS_DIR) / "locations.csv",
    payroll_id_column: Optional[str] = None,
) -> Dict[str, Dict[str, Optional[str]]]:
    """Load headcount data from an Excel spreadsheet.

    The resulting mapping is keyed by payroll ID and provides the
    driver's name, email, phone number, and a location tag ID when
    available.
    """
    df = pd.read_excel(xlsx_path)
    df.columns = [str(c).strip() for c in df.columns]

    # Discover payroll ID column if not provided
    if payroll_id_column and payroll_id_column in df.columns:
        id_col = payroll_id_column
    else:
        id_col = None
        for col in [
            "Payroll_ID",
            "Payroll ID",
            "Employee_ID",
            "Employee ID",
            "Route#",
        ]:
            if col in df.columns:
                id_col = col
                break
    if not id_col:
        raise ValueError("Payroll ID column not found in spreadsheet")

    email_col = "Work_Email" if "Work_Email" in df.columns else "Email"
    phone_col = "Primary_Phone" if "Primary_Phone" in df.columns else "Phone"
    first_col = "Legal_Firstname" if "Legal_Firstname" in df.columns else None
    last_col = "Legal_Lastname" if "Legal_Lastname" in df.columns else None

    location_col = None
    for col in ["Work_Location", "Location_Code", "Location_Desc", "Location"]:
        if col in df.columns:
            location_col = col
            break

    loc_map = {}
    try:
        loc_df = pd.read_csv(locations_csv)
        for _, row in loc_df.iterrows():
            loc_map[str(row["location"]).strip()] = str(row["id"])
    except FileNotFoundError:
        pass

    mapping: Dict[str, Dict[str, Optional[str]]] = {}
    for _, row in df.iterrows():
        pid = row.get(id_col)
        if pd.isna(pid):
            continue
        if isinstance(pid, float) and math.isclose(pid % 1, 0):
            pid = int(pid)
        pid_str = str(pid)

        email = row.get(email_col)
        if pd.isna(email):
            email = None
        else:
            email = str(email).strip()

        phone = row.get(phone_col)
        if pd.isna(phone):
            phone = None
        else:
            phone = str(int(phone)) if isinstance(phone, float) else str(phone).strip()

        loc_tag = None
        if location_col:
            loc_val = row.get(location_col)
            if not pd.isna(loc_val):
                loc_tag = loc_map.get(str(loc_val).strip())

        name = None
        if first_col and last_col:
            first = row.get(first_col)
            last = row.get(last_col)
            if not pd.isna(first) and not pd.isna(last):
                name = f"{str(first).strip()} {str(last).strip()}"

        mapping[pid_str] = {
            "name": name,
            "email": email,
            "phone": phone,
            "location_tag_id": loc_tag,
        }

    return mapping
