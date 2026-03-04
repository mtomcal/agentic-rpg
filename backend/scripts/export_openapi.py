"""Export the FastAPI OpenAPI schema to a JSON file."""

import json
import sys
from pathlib import Path

# Add src to path so agentic_rpg is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agentic_rpg.main import app  # noqa: E402

output_path = Path(__file__).resolve().parent.parent / "openapi.json"

with open(output_path, "w") as f:
    json.dump(app.openapi(), f, indent=2)

print(f"OpenAPI schema written to {output_path}")
