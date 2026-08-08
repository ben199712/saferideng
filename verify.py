import os, subprocess, json, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {"returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr}

staged_files = run(["git","--no-pager","diff","--cached","--name-only"])
stat = run(["git","--no-pager","diff","--cached","--stat"])

# Search for any Resend API keys with regex pattern in index
re_pattern_check = run(["git","--no-pager","grep","--cached","-n","-E","re_[A-Za-z0-9_\\-]{14,}"])
sk_pattern = run(["git","--no-pager","grep","--cached","-n","-E","sk-[A-Za-z0-9_\\-]{16,}"])

# Ensure private_media tracked?
pm_tracked = run(["git","ls-files","--cached","private_media/","private_media_backup/","vehicle_qrcodes/"])
refact_tracked = run(["git","ls-files","--cached",".refact/",".freebuff/"])

results = {
    "staged_count": sum(1 for _ in (staged_files.get("stdout") or "").strip().splitlines() if _),
    "staged_files": (staged_files.get("stdout") or "").strip().splitlines()[:250],
    "stat": (stat.get("stdout") or ""),
    "re_pattern_check": re_pattern_check,
    "sk_pattern": sk_pattern,
    "pm_tracked_files": (pm_tracked.get("stdout") or "").strip().splitlines(),
    "refact_tracked_files_count": sum(1 for ln in (refact_tracked.get("stdout") or "").splitlines() if ln),
}
with open(os.path.join(ROOT, "verify.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)
print("wrote verify.json")
