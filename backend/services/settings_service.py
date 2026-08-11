"""
Runtime-editable system settings, backed by the Setting table.
Falls back to config.py defaults if a key has never been set.
"""
import json
import backend.config as config
from backend.extensions import db
from backend.models import Setting


def _get(key, default):
    row = Setting.query.filter_by(key=key).first()
    if not row:
        return default
    try:
        return json.loads(row.value)
    except (TypeError, ValueError):
        return default


def _set(key, value):
    row = Setting.query.filter_by(key=key).first()
    if not row:
        row = Setting(key=key, value=json.dumps(value))
        db.session.add(row)
    else:
        row.value = json.dumps(value)
    db.session.commit()


def get_sla_minutes():
    return _get("sla_minutes", dict(config.SLA_MINUTES))


def set_sla_minutes(mapping):
    """mapping: {priority: minutes}"""
    current = get_sla_minutes()
    for p in config.PRIORITIES:
        if p in mapping:
            current[p] = int(mapping[p])
    _set("sla_minutes", current)
    return current


def get_workload_capacity():
    return _get("workload_capacity", config.WORKLOAD_CAPACITY)


def set_workload_capacity(value):
    _set("workload_capacity", int(value))
    return int(value)


def get_auto_close_days():
    return _get("auto_close_days", 3)


def set_auto_close_days(value):
    _set("auto_close_days", int(value))
    return int(value)


def get_sla_labels():
    minutes = get_sla_minutes()
    labels = {}
    for p, m in minutes.items():
        if m % (24 * 60) == 0 and m >= 24 * 60:
            labels[p] = f"{m // (24 * 60)} days"
        elif m % 60 == 0:
            labels[p] = f"{m // 60} hours"
        else:
            labels[p] = f"{m} minutes"
    return labels