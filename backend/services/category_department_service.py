"""
Manages the dynamic list of categories and departments, super-admin only.
Falls back to config.py's static lists if nothing's been added yet, so
existing data/routes keep working untouched.
"""
import backend.config as config
from backend.extensions import db
from backend.models import Category, DepartmentRecord


def _seed_if_empty(model, seed_list):
    if model.query.count() == 0:
        for key in seed_list:
            db.session.add(model(key=key, label=key.replace('_', ' ').title() if model is Category else key))
        db.session.commit()


def list_categories(active_only=True):
    _seed_if_empty(Category, config.CATEGORIES)
    q = Category.query
    if active_only:
        q = q.filter_by(is_active=True)
    return [c.key for c in q.order_by(Category.label).all()]


def list_category_records():
    _seed_if_empty(Category, config.CATEGORIES)
    return Category.query.order_by(Category.label).all()


def add_category(key, label):
    key = key.strip().lower().replace(" ", "_")
    label = label.strip()
    if not key or not label:
        raise ValueError("Category key and label are required.")
    if Category.query.filter_by(key=key).first():
        raise ValueError("A category with this key already exists.")
    db.session.add(Category(key=key, label=label))
    db.session.commit()


def toggle_category(category_id):
    c = db.session.get(Category, category_id)
    if not c:
        raise ValueError("Category not found.")
    c.is_active = not c.is_active
    db.session.commit()
    return c


def list_departments(active_only=True):
    _seed_if_empty(DepartmentRecord, config.DEPARTMENTS)
    q = DepartmentRecord.query
    if active_only:
        q = q.filter_by(is_active=True)
    return [d.key for d in q.order_by(DepartmentRecord.label).all()]


def list_department_records():
    _seed_if_empty(DepartmentRecord, config.DEPARTMENTS)
    return DepartmentRecord.query.order_by(DepartmentRecord.label).all()


def add_department(key, label=None):
    key = key.strip()
    label = (label or key).strip()
    if not key:
        raise ValueError("Department name is required.")
    if DepartmentRecord.query.filter_by(key=key).first():
        raise ValueError("A department with this name already exists.")
    db.session.add(DepartmentRecord(key=key, label=label))
    db.session.commit()


def toggle_department(department_id):
    d = db.session.get(DepartmentRecord, department_id)
    if not d:
        raise ValueError("Department not found.")
    d.is_active = not d.is_active
    db.session.commit()
    return d