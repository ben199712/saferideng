import os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

# All files to restore from origin/main exactly (no corruption)
REL_PATHS = [
    "accounts/migrations/0001_initial.py",
    "apps/emergency/migrations/0001_initial.py",
    "apps/emergency/migrations/0002_initial.py",
    "apps/emergency/migrations/0003_sos_authority_contacts.py",
    "apps/emergency/migrations/0004_rename_emergency_s_alert_i_5f4c7b_idx_emergency_s_alert_i_6465f1_idx_and_more.py",
    "apps/reports/migrations/0001_initial.py",
    "apps/reports/migrations/0002_initial.py",
    "apps/tracking/migrations/0001_initial.py",
    "apps/tracking/migrations/0002_tripshare_broadcaster_token.py",
    "apps/tracking/migrations/0003_rename_apps_tracking_locationtrip_share_timestamp_2008a2_idx_tracking_lo_trip_sh_55e652_idx.py",
    "apps/trips/migrations/0001_initial.py",
    "apps/vehicles/migrations/0001_initial.py",
    "apps/vehicles/migrations/0002_vehicle_vin.py",
    "core/migrations/0001_email_notification_log.py",
    "core/migrations/0002_rename_core_email_event_ty_8ee15e_idx_core_emailn_event_t_7b7347_idx_and_more.py",
    "drivers/migrations/0001_initial.py",
    "drivers/migrations/0002_driverprofile_safety_upgrade.py",
    "drivers/migrations/0003_driverdocument.py",
    "drivers/migrations/0004_rename_drivers_dri_user_id_7ad19a_idx_drivers_dri_user_id_c9ceb0_idx_and_more.py",
    "apps/tracking/tests.py",
    "apps/trips/tests.py",
    "drivers/tests.py",
]
restored = []
skipped = []
for rel in REL_PATHS:
    try:
        r = subprocess.run(["git","--no-pager","show","origin/main:" + rel.replace("\\","/")], capture_output=True, check=True)
        dest = ROOT / rel.replace("/", os.sep)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.stdout)
        restored.append(rel)
    except subprocess.CalledProcessError as exc:
        skipped.append((rel, "retcode=" + str(exc.returncode) + " " + (exc.stderr.decode(errors='replace')[:200] if exc.stderr else "")))
    except Exception as exc2:
        skipped.append((rel, str(exc2)))

p = ROOT / "_restore_report.json"
import json
with open(p, "w", encoding="utf-8") as f:
    json.dump({"restored_count": len(restored), "restored": restored, "skipped": skipped}, f, indent=2)
print("RESTORED", len(restored), "/ SKIPPED", len(skipped))
sys.exit(0 if not skipped else 2)
