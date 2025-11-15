# debug_imports.py
import os
import sys
from pathlib import Path
import traceback

print("=== debug_imports.py ===")
print("Current working directory:")
print("  ", os.getcwd())
print()

print("First 10 entries of sys.path:")
for i, p in enumerate(sys.path[:10]):
    print(f"  {i:02d}: {p}")
print()

project_root = Path(__file__).resolve().parent
print("Project root (debug file location):", project_root)
print("Files and folders at project root:")
for p in sorted(project_root.iterdir()):
    print("  -", p.name)
print()

# Check app folder exists and its contents
app_dir = project_root / "app"
print("app folder exists:", app_dir.exists())
if app_dir.exists():
    print(" app/ files (top-level):")
    for p in sorted(app_dir.iterdir()):
        print("   -", p.name)
print()

# Try to import app.services
print("Attempting: import app.services ...")
try:
    import app.services
    print("import OK: app.services ->", app.services)
except Exception as e:
    print("import failed:")
    traceback.print_exc()
