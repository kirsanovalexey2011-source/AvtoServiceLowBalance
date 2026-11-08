"""Extract embedded AutoFlow JavaScript for Node syntax checks."""
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.web import PAGE
from app.marketplace_web import MARKETPLACE, PARTNER, PLATFORM

def extract(page: str, destination: Path, label: str) -> None:
    match = re.search(r"<script>(.*?)</script>", page, flags=re.DOTALL)
    if not match:
        raise SystemExit(f"{label} script block not found")
    destination.write_text(match.group(1), encoding="utf-8")
    print(f"Extracted {label} script to {destination}")

base = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/autoflow")
extract(PAGE, Path(str(base) + "-dashboard.js"), "dashboard")
extract(MARKETPLACE, Path(str(base) + "-marketplace.js"), "marketplace")
extract(PARTNER, Path(str(base) + "-partner.js"), "partner")
extract(PLATFORM, Path(str(base) + "-platform.js"), "platform")
