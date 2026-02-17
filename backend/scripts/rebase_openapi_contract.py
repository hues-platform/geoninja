import json
from pathlib import Path

from geoninja_backend.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]

OUT = REPO_ROOT / "contracts" / "openapi.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

spec = app.openapi()
OUT.write_text(json.dumps(spec, indent=2))

print(f"[ok] Wrote OpenAPI contract to {OUT}")
