import json
import os
from datetime import datetime
from copy import deepcopy

LEARNING_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "learning_config.json")

VARIABLE_ORDER = ["hook_ranking", "cta_ranking", "hashtag_ranking"]

DEFAULT_CONFIG = {
    "hook_templates": [],
    "cta_pool": [],
    "hashtag_pool": [],
    "variable_rotation_index": 0,
    "updated_at": None,
}


def load_learning_config(path: str = None) -> dict:
    if path is None:
        path = LEARNING_CONFIG_PATH
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cfg = deepcopy(DEFAULT_CONFIG)
        save_learning_config(path, cfg)
        return cfg


def save_learning_config(path: str, config: dict):
    config["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def compute_learning_config(current_config: dict, classifications: list, analytics_records: list) -> tuple:
    if len(classifications) < 3:
        return current_config, None

    config = deepcopy(current_config)
    rotation_index = config.get("variable_rotation_index", 0)
    variable = VARIABLE_ORDER[rotation_index % len(VARIABLE_ORDER)]

    viral_ids = {c["post_id"] for c in classifications if c["classification"] == "viral"}

    iteration = None
    if variable == "hook_ranking":
        iteration = _rank_list(config, analytics_records, viral_ids, "hook_templates")
    elif variable == "cta_ranking":
        iteration = _rank_list(config, analytics_records, viral_ids, "cta_pool")
    elif variable == "hashtag_ranking":
        iteration = _rank_list(config, analytics_records, viral_ids, "hashtag_pool")

    if iteration:
        config["variable_rotation_index"] = (rotation_index + 1) % len(VARIABLE_ORDER)

    return config, iteration


def _rank_list(config: dict, analytics_records: list, viral_ids: set, pool_key: str) -> dict:
    if pool_key not in config or not config[pool_key]:
        return None

    old_value = deepcopy(config[pool_key])
    pool = config[pool_key]

    scored = []
    for item in pool:
        if isinstance(item, str):
            count = sum(1 for pid in viral_ids for r in analytics_records
                        if r.get("post_id") == pid and item.lower() in str(r).lower())
        else:
            count = 0
        scored.append((count, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    config[pool_key] = [item for _, item in scored]

    if old_value == config[pool_key]:
        return None

    return {
        "id": f"iter-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "variable_changed": pool_key,
        "previous_value": old_value,
        "new_value": deepcopy(config[pool_key]),
        "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
