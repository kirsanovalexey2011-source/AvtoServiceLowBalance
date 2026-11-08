"""Extract the embedded dashboard JavaScript so CI can syntax-check it with Node."""
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.web import PAGE

match = re.search(r"<script>(.*?)</script>", PAGE, flags=re.DOTALL)
if not match:
    raise SystemExit("Dashboard script block not found")
destination = Path(sys.argv[1] if len(sys.argv) > 1 else "dashboard.js")
destination.write_text(match.group(1), encoding="utf-8")
print(f"Extracted dashboard script to {destination}")
