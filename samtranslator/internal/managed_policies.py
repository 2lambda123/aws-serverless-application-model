import json
import os
from pathlib import Path
from typing import Dict, Optional

with Path(os.path.dirname(os.path.abspath(__file__)), "data", "managed_policies.json").open(encoding="utf-8") as f:
    _BUNDLED_MANAGED_POLICIES: Dict[str, Dict[str, str]] = json.load(f)


def get_bundled_managed_policy_map(partition: str) -> Optional[Dict[str, str]]:
    return _BUNDLED_MANAGED_POLICIES.get(partition)
