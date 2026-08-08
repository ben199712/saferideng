import os, re, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
mig_files = {}
for p in ROOT.rglob("migrations/[0-9]*_*.py"):
    if "venv" in str(p).lower() or "__pycache__" in str(p):
        continue
    try:
        rel = p.relative_to(ROOT).as_posix()
        # app label is the directory name just before migrations/
        app_label = p.relative_to(ROOT).parts[0] if str(p.relative_to(ROOT)).count("/") >= 2 else rel.split("/")[0]
        # Actually: apps/<name>/migrations → app_label is apps/xxx? No, Django app_label from INSTALLED_APPS!
        # Determine INSTALLED_APP label correctly: use migrations folder parent name if folder name is 'migrations'
        parent_dirs = list(p.relative_to(ROOT).parts)[:-2]  # strip filename.py + migrations/
        if len(parent_dirs) == 1:
            app_label = parent_dirs[0]
        elif len(parent_dirs) == 2 and parent_dirs[0] == "apps":
            app_label = parent_dirs[1]  # e.g. emergency, tracking under apps/
        else:
            # something else
            app_label = parent_dirs[-1]
        name = p.stem
        text = p.read_text(encoding="utf-8")
        # find dependencies list
        deps = []
        m = re.search(r"dependencies\s*=\s*\[([\s\S]*?)\]", text, re.M)
        if m:
            dep_content = m.group(1)
            # find tuples like ('x','y')
            for dep in re.finditer(r"\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", dep_content):
                deps.append((dep.group(1), dep.group(2)))
        mig_files.setdefault(app_label, {})[name] = {"file": rel, "deps": deps}
    except Exception as e:
        print("ERR reading", p, e, file=sys.stderr)

# Normalize app label mapping: for any found app label, get all files
all_nodes = {}
for app, migs in mig_files.items():
    for name, info in migs.items():
        all_nodes[(app, name)] = info
missing = {}
for (app, name), info in all_nodes.items():
    for dep in info["deps"]:
        if dep not in all_nodes:
            missing.setdefault((app, name), []).append(dep)

report = {
    "all_migrations_count": len(all_nodes),
    "all_nodes_keys": sorted([f"{a}.{n}" for (a,n) in all_nodes.keys()]),
    "migrations_per_app": {a: sorted(list(m.keys())) for a,m in mig_files.items()},
    "missing_dependencies_per_migration": {f"{a}.{n}": [f"{x}.{y}" for (x,y) in ds] for (a,n),ds in missing.items()},
}
with open(ROOT/"_migcheck.json","w",encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print("WROTE _migcheck.json entries:", len(all_nodes), "missing:", sum(len(v) for v in missing.values()))
sys.exit(0 if not missing else 1)
