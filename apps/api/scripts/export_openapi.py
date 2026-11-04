"""Writes the OpenAPI schema to apps/api/openapi.json (consumed by `pnpm gen:api` in apps/web)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app  # noqa: E402

out = Path(__file__).resolve().parents[1] / "openapi.json"
out.write_text(json.dumps(create_app().openapi(), indent=2))
print(f"Wrote {out}")
