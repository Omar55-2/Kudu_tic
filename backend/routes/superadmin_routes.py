from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

import backend.config as config
from backend.extensions import db
from backend.models import User
from backend.services import settings_service, category_department_service
from backend.utils import super_admin_required, is_valid_email

superadmin_bp = Blueprint("superadmin", __name__, url_prefix="/super-admin")


@superadmin_bp.route("/")
@login_required
@super_admin_required
def panel():
    return render_template(
        "superadmin/panel.html",
        sla_minutes=settings_service.get_sla_minutes(),
        workload_capacity=settings_service.get_workload_capacity(),
        auto_close_days=settings_service.get_auto_close_days(),
        priorities=config.PRIORITIES,
        priority_labels=config.PRIORITY_LABELS,
        categories=category_department_service.list_category_records(),
        departments=category_department_service.list_department_records(),
    )


@superadmin_bp.route("/settings/sla", methods=["POST"])
@login_required
@super_admin_required
def update_sla():
    mapping = {}
    for p in config.PRIORITIES:
        raw = request.form.get(f"sla_{p}")
        if raw:
            try:
                mapping[p] = int(raw)
            except ValueError:
                flash(f"Invalid minutes value for {p}.", "error")
                return redirect(url_for("superadmin.panel"))
    settings_service.set_sla_minutes(mapping)
    flash("SLA policy updated.", "success")
    return redirect(url_for("superadmin.panel"))


@superadmin_bp.route("/settings/workload", methods=["POST"])
@login_required
@super_admin_required
def update_workload():
    try:
        cap = int(request.form.get("workload_capacity", 20))
    except ValueError:
        flash("Invalid capacity value.", "error")
        return redirect(url_for("superadmin.panel"))
    settings_service.set_workload_capacity(cap)
    flash("Workload capacity updated.", "success")
    return redirect(url_for("superadmin.panel"))


@superadmin_bp.route("/settings/auto-close", methods=["POST"])
@login_required
@super_admin_required
def update_auto_close():
    try:
        days = int(request.form.get("auto_close_days", 3))
    except ValueError:
        flash("Invalid value.", "error")
        return redirect(url_for("superadmin.panel"))
    settings_service.set_auto_close_days(days)
    flash("Auto-close window updated.", "success")
    return redirect(url_for("superadmin.panel"))


@superadmin_bp.route("/categories/add", methods=["POST"])
@login_required
@super_admin_required
def add_category():
    try:
        category_department_service.add_category(
            request.form.get("key", ""), request.form.get("label", "")
        )
        flash("Category added.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("superadmin.panel"))


@superadmin_bp.route("/categories/<int:category_id>/toggle", methods=["POST"])
@login_required
@super_admin_required
def toggle_category(category_id):
    try:
        category_department_service.toggle_category(category_id)
        flash("Category updated.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("superadmin.panel"))


@superadmin_bp.route("/departments/add", methods=["POST"])
@login_required
@super_admin_required
def add_department():
    try:
        category_department_service.add_department(request.form.get("key", ""))
        flash("Department added.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("superadmin.panel"))


@superadmin_bp.route("/departments/<int:department_id>/toggle", methods=["POST"])
@login_required
@super_admin_required
def toggle_department(department_id):
    try:
        category_department_service.toggle_department(department_id)
        flash("Department updated.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("superadmin.panel"))


@superadmin_bp.route("/employees/add", methods=["POST"])
@login_required
@super_admin_required
def add_employee():
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    department = request.form.get("department", "Support")
    role = request.form.get("role", "employee")

    if not full_name or not email or not password:
        flash("Full name, email, and password are required.", "error")
        return redirect(url_for("superadmin.panel"))
    if not is_valid_email(email):
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("superadmin.panel"))
    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("superadmin.panel"))
    if User.query.filter_by(email=email).first():
        flash("An account with this email already exists.", "error")
        return redirect(url_for("superadmin.panel"))
    if department not in config.DEPARTMENTS:
        department = "Support"
    if role not in ("employee", "admin", "super_admin"):
        role = "employee"

    user = User(
        full_name=full_name, email=email, department=department,
        role=role, email_verified=True,  # created by super admin — pre-verified
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash(f"{full_name} was added directly and can log in immediately.", "success")
    return redirect(url_for("superadmin.panel"))