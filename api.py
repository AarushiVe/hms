from datetime import date, datetime, timedelta

from flask import Blueprint, g, request
from sqlalchemy import or_

from .auth import auth_required, issue_token, revoke_token
from .extensions import cache, db
from .models import (
    Appointment,
    AppointmentStatus,
    Department,
    DoctorAvailability,
    DoctorProfile,
    Notification,
    Treatment,
    User,
    UserRole,
)
from .utils import parse_date

api_bp = Blueprint("api", __name__, url_prefix="/api")


def user_payload(user):
    data = {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
    }
    if user.role == UserRole.DOCTOR and user.doctor_profile:
        data["specialization"] = user.doctor_profile.specialization
        data["bio"] = user.doctor_profile.bio
    return data


def username_or_email_exists(username, email=None):
    conditions = [User.username == username]
    if email:
        conditions.append(User.email == email)
    return User.query.filter(or_(*conditions)).first() is not None


def _time_to_minutes(value: str):
    hh, mm = value.split(":")
    return (int(hh) * 60) + int(mm)


def _is_half_hour_time(value: str):
    try:
        parts = value.split(":")
        if len(parts) != 2:
            return False
        hh = int(parts[0])
        mm = int(parts[1])
        if hh < 0 or hh > 23:
            return False
        return mm in (0, 30)
    except Exception:
        return False


def _is_valid_slot_window(start_time: str, end_time: str):
    if not _is_half_hour_time(start_time) or not _is_half_hour_time(end_time):
        return False
    return _time_to_minutes(start_time) < _time_to_minutes(end_time)


def _is_time_within_slot(slot, appointment_time: str):
    if not _is_half_hour_time(appointment_time):
        return False
    appt_minutes = _time_to_minutes(appointment_time)
    slot_start = _time_to_minutes(slot.start_time)
    slot_end = _time_to_minutes(slot.end_time)
    return slot_start <= appt_minutes < slot_end


@api_bp.get("/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat()}


@api_bp.post("/auth/register")
def register_patient():
    data = request.get_json(force=True)
    required = ["username", "password", "name"]
    if any(not data.get(k) for k in required):
        return {"error": "username, password, name are required"}, 400

    email = data.get("email")
    if username_or_email_exists(data["username"], email):
        return {"error": "Username or email already exists"}, 409

    patient = User(
        username=data["username"],
        name=data["name"],
        email=data.get("email"),
        phone=data.get("phone"),
        role=UserRole.PATIENT,
    )
    patient.set_password(data["password"])
    db.session.add(patient)
    db.session.commit()
    return {"message": "Patient registered successfully"}, 201


@api_bp.post("/auth/login")
def login():
    data = request.get_json(force=True)
    username = data.get("username", "")
    password = data.get("password", "")

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return {"error": "Invalid credentials"}, 401
    if not user.is_active:
        return {"error": "User is blocked"}, 403

    token = issue_token(user)
    return {
        "token": token.token,
        "expires_at": token.expires_at.isoformat(),
        "user": user_payload(user),
    }


@api_bp.post("/auth/logout")
@auth_required()
def logout():
    revoke_token(g.current_token)
    return {"message": "Logged out"}


@api_bp.get("/me")
@auth_required()
def me():
    return {"user": user_payload(g.current_user)}


@api_bp.get("/departments")
@auth_required()
@cache.cached(timeout=300)
def departments():
    return {
        "items": [
            {"id": d.id, "name": d.name, "description": d.description}
            for d in Department.query.order_by(Department.name).all()
        ]
    }


@api_bp.get("/notifications")
@auth_required()
def notifications():
    items = Notification.query.filter_by(user_id=g.current_user.id).order_by(Notification.created_at.desc()).limit(20).all()
    return {
        "items": [
            {
                "id": n.id,
                "kind": n.kind,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in items
        ]
    }


@api_bp.get("/admin/summary")
@auth_required([UserRole.ADMIN])
@cache.cached(timeout=120)
def admin_summary():
    return {
        "doctors": User.query.filter_by(role=UserRole.DOCTOR).count(),
        "patients": User.query.filter_by(role=UserRole.PATIENT).count(),
        "appointments": Appointment.query.count(),
        "today_appointments": Appointment.query.filter_by(date=date.today()).count(),
    }


@api_bp.get("/admin/doctors")
@auth_required([UserRole.ADMIN])
def list_doctors_admin():
    q = request.args.get("q", "").strip()
    active_only = request.args.get("active_only", "1") == "1"
    query = User.query.filter_by(role=UserRole.DOCTOR)
    if active_only:
        query = query.filter(User.is_active.is_(True))
    if q:
        query = query.join(DoctorProfile).filter(
            or_(User.name.ilike(f"%{q}%"), DoctorProfile.specialization.ilike(f"%{q}%"))
        )
    doctors = query.order_by(User.name).all()
    return {"items": [user_payload(d) for d in doctors]}


@api_bp.post("/admin/doctors")
@auth_required([UserRole.ADMIN])
def create_doctor_admin():
    data = request.get_json(force=True)
    required = ["username", "password", "name", "specialization"]
    if any(not data.get(k) for k in required):
        return {"error": "username, password, name, specialization are required"}, 400

    email = data.get("email")
    if username_or_email_exists(data["username"], email):
        return {"error": "Username or email exists"}, 409

    doctor = User(
        username=data["username"],
        name=data["name"],
        role=UserRole.DOCTOR,
        email=data.get("email"),
        phone=data.get("phone"),
    )
    doctor.set_password(data["password"])
    db.session.add(doctor)
    db.session.flush()

    profile = DoctorProfile(
        user_id=doctor.id,
        specialization=data["specialization"],
        bio=data.get("bio", ""),
        department_id=data.get("department_id"),
    )
    db.session.add(profile)
    db.session.commit()
    cache.clear()
    return {"message": "Doctor created", "doctor": user_payload(doctor)}, 201


@api_bp.put("/admin/doctors/<int:doctor_id>")
@auth_required([UserRole.ADMIN])
def update_doctor_admin(doctor_id):
    data = request.get_json(force=True)
    doctor = User.query.filter_by(id=doctor_id, role=UserRole.DOCTOR).first_or_404()

    doctor.name = data.get("name", doctor.name)
    doctor.email = data.get("email", doctor.email)
    doctor.phone = data.get("phone", doctor.phone)
    if data.get("is_active") is not None:
        doctor.is_active = bool(data.get("is_active"))

    if doctor.doctor_profile:
        doctor.doctor_profile.specialization = data.get("specialization", doctor.doctor_profile.specialization)
        doctor.doctor_profile.bio = data.get("bio", doctor.doctor_profile.bio)
        doctor.doctor_profile.department_id = data.get("department_id", doctor.doctor_profile.department_id)

    db.session.commit()
    cache.clear()
    return {"message": "Doctor updated", "doctor": user_payload(doctor)}


@api_bp.delete("/admin/doctors/<int:doctor_id>")
@auth_required([UserRole.ADMIN])
def disable_doctor_admin(doctor_id):
    doctor = User.query.filter_by(id=doctor_id, role=UserRole.DOCTOR).first_or_404()
    doctor.is_active = False
    db.session.commit()
    return {"message": "Doctor disabled"}


@api_bp.get("/admin/appointments")
@auth_required([UserRole.ADMIN])
def all_appointments_admin():
    items = Appointment.query.order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    return {
        "items": [
            {
                "id": a.id,
                "date": a.date.isoformat(),
                "time": a.time,
                "status": a.status,
                "doctor": a.doctor.name,
                "patient": a.patient.name,
                "diagnosis": a.treatment.diagnosis if a.treatment else None,
            }
            for a in items
        ]
    }


@api_bp.get("/admin/search")
@auth_required([UserRole.ADMIN])
def admin_search():
    q = request.args.get("q", "").strip()
    if not q:
        return {"patients": [], "doctors": []}

    patients = User.query.filter(
        User.role == UserRole.PATIENT,
        or_(
            User.name.ilike(f"%{q}%"),
            User.username.ilike(f"%{q}%"),
            User.phone.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%"),
            User.id == (int(q) if q.isdigit() else -1),
        ),
    ).all()

    doctors = (
        User.query.join(DoctorProfile)
        .filter(
            User.role == UserRole.DOCTOR,
            or_(User.name.ilike(f"%{q}%"), DoctorProfile.specialization.ilike(f"%{q}%")),
        )
        .all()
    )

    return {"patients": [user_payload(x) for x in patients], "doctors": [user_payload(x) for x in doctors]}


@api_bp.patch("/admin/users/<int:user_id>/status")
@auth_required([UserRole.ADMIN])
def set_user_status_admin(user_id):
    data = request.get_json(force=True)
    user = User.query.get_or_404(user_id)
    if user.role == UserRole.ADMIN:
        return {"error": "Cannot disable admin"}, 400
    user.is_active = bool(data.get("is_active", True))
    db.session.commit()
    return {"message": "Status updated", "user": user_payload(user)}


@api_bp.put("/admin/doctors/<int:doctor_id>/availability")
@auth_required([UserRole.ADMIN])
def admin_doctor_availability_update(doctor_id):
    doctor = User.query.filter_by(id=doctor_id, role=UserRole.DOCTOR).first_or_404()
    data = request.get_json(force=True)
    days = data.get("days", [])
    if not isinstance(days, list) or not days:
        return {"error": "days must be a non-empty array"}, 400

    for day in days:
        if not day.get("date"):
            return {"error": "date is required for each slot"}, 400
        d = parse_date(day["date"])
        if d < date.today() or d > date.today() + timedelta(days=30):
            return {"error": "Admin can create availability only for next 30 days"}, 400
        if not _is_valid_slot_window(day.get("start_time", "09:00"), day.get("end_time", "17:00")):
            return {"error": "Slot times must be in 30-minute format and end must be after start"}, 400

    for day in days:
        d = parse_date(day["date"])
        item = DoctorAvailability.query.filter_by(doctor_id=doctor.id, available_date=d).first()
        if not item:
            item = DoctorAvailability(doctor_id=doctor.id, available_date=d, start_time="09:00", end_time="17:00")
            db.session.add(item)
        item.start_time = day.get("start_time", item.start_time)
        item.end_time = day.get("end_time", item.end_time)
        item.is_available = bool(day.get("is_available", True))

    db.session.add(
        Notification(
            user_id=doctor.id,
            kind="slot_update",
            message=f"Admin updated your availability slots for {len(days)} day(s).",
        )
    )
    db.session.commit()
    cache.delete_memoized(patient_doctors_list)
    return {"message": f"Availability updated for Dr. {doctor.name}"}


@api_bp.get("/doctor/dashboard")
@auth_required([UserRole.DOCTOR])
def doctor_dashboard():
    today = date.today()
    end = today + timedelta(days=7)
    doctor = g.current_user

    upcoming = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date >= today,
        Appointment.date <= end,
    ).order_by(Appointment.date.asc(), Appointment.time.asc()).all()

    unique_patient_ids = sorted({a.patient_id for a in upcoming})
    patients = User.query.filter(User.id.in_(unique_patient_ids)).all() if unique_patient_ids else []

    return {
        "upcoming": [
            {
                "id": a.id,
                "date": a.date.isoformat(),
                "time": a.time,
                "status": a.status,
                "patient_id": a.patient_id,
                "patient_name": a.patient.name,
            }
            for a in upcoming
        ],
        "patients": [user_payload(p) for p in patients],
    }


@api_bp.get("/doctor/appointments")
@auth_required([UserRole.DOCTOR])
def doctor_appointments():
    doctor_id = g.current_user.id
    items = Appointment.query.filter_by(doctor_id=doctor_id).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    return {
        "items": [
            {
                "id": a.id,
                "date": a.date.isoformat(),
                "time": a.time,
                "status": a.status,
                "patient_name": a.patient.name,
                "patient_id": a.patient_id,
                "treatment": {
                    "diagnosis": a.treatment.diagnosis,
                    "prescription": a.treatment.prescription,
                    "notes": a.treatment.notes,
                }
                if a.treatment
                else None,
            }
            for a in items
        ]
    }


@api_bp.patch("/doctor/appointments/<int:appointment_id>/status")
@auth_required([UserRole.DOCTOR])
def update_appointment_status(appointment_id):
    data = request.get_json(force=True)
    status = data.get("status")
    if status not in [AppointmentStatus.BOOKED, AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
        return {"error": "Invalid status"}, 400

    appt = Appointment.query.filter_by(id=appointment_id, doctor_id=g.current_user.id).first_or_404()
    appt.status = status
    db.session.commit()
    return {"message": "Status updated"}


@api_bp.post("/doctor/appointments/<int:appointment_id>/treatment")
@auth_required([UserRole.DOCTOR])
def add_treatment(appointment_id):
    appt = Appointment.query.filter_by(id=appointment_id, doctor_id=g.current_user.id).first_or_404()
    data = request.get_json(force=True)

    if not data.get("diagnosis") or not data.get("prescription"):
        return {"error": "diagnosis and prescription are required"}, 400

    if appt.treatment:
        treatment = appt.treatment
        treatment.diagnosis = data["diagnosis"]
        treatment.prescription = data["prescription"]
        treatment.notes = data.get("notes", "")
        treatment.next_visit_date = parse_date(data["next_visit_date"]) if data.get("next_visit_date") else None
    else:
        treatment = Treatment(
            appointment_id=appt.id,
            diagnosis=data["diagnosis"],
            prescription=data["prescription"],
            notes=data.get("notes", ""),
            next_visit_date=parse_date(data["next_visit_date"]) if data.get("next_visit_date") else None,
        )
        db.session.add(treatment)

    appt.status = AppointmentStatus.COMPLETED
    db.session.add(
        Notification(
            user_id=appt.patient_id,
            kind="treatment",
            message=f"Treatment updated for appointment #{appt.id} by Dr. {g.current_user.name}.",
        )
    )
    db.session.commit()
    return {"message": "Treatment saved"}


@api_bp.get("/doctor/patients/<int:patient_id>/history")
@auth_required([UserRole.DOCTOR])
def patient_history_for_doctor(patient_id):
    appts = (
        Appointment.query.filter_by(patient_id=patient_id, doctor_id=g.current_user.id)
        .filter(Appointment.status == AppointmentStatus.COMPLETED)
        .order_by(Appointment.date.desc())
        .all()
    )
    return {
        "items": [
            {
                "appointment_id": a.id,
                "date": a.date.isoformat(),
                "diagnosis": a.treatment.diagnosis if a.treatment else None,
                "prescription": a.treatment.prescription if a.treatment else None,
                "notes": a.treatment.notes if a.treatment else None,
            }
            for a in appts
        ]
    }


@api_bp.put("/doctor/availability")
@auth_required([UserRole.DOCTOR])
def doctor_availability_update():
    data = request.get_json(force=True)
    days = data.get("days", [])
    if not isinstance(days, list):
        return {"error": "days must be an array"}, 400

    for day in days:
        d = parse_date(day["date"])
        if d < date.today() or d > date.today() + timedelta(days=7):
            return {"error": "Availability can only be set for next 7 days"}, 400
        if not _is_valid_slot_window(day.get("start_time", "09:00"), day.get("end_time", "17:00")):
            return {"error": "Slot times must be in 30-minute format and end must be after start"}, 400

    for day in days:
        d = parse_date(day["date"])
        item = DoctorAvailability.query.filter_by(doctor_id=g.current_user.id, available_date=d).first()
        if not item:
            item = DoctorAvailability(doctor_id=g.current_user.id, available_date=d, start_time="09:00", end_time="17:00")
            db.session.add(item)
        item.start_time = day.get("start_time", item.start_time)
        item.end_time = day.get("end_time", item.end_time)
        item.is_available = bool(day.get("is_available", True))

    db.session.commit()
    cache.delete_memoized(patient_doctors_list)
    return {"message": "Availability updated"}


@api_bp.get("/patient/dashboard")
@auth_required([UserRole.PATIENT])
def patient_dashboard():
    pid = g.current_user.id
    upcoming = Appointment.query.filter(
        Appointment.patient_id == pid,
        Appointment.date >= date.today(),
    ).order_by(Appointment.date.asc(), Appointment.time.asc()).all()

    history = (
        Appointment.query.filter_by(patient_id=pid)
        .filter(Appointment.date < date.today())
        .order_by(Appointment.date.desc(), Appointment.time.desc())
        .limit(10)
        .all()
    )

    return {
        "upcoming": [
            {
                "id": a.id,
                "date": a.date.isoformat(),
                "time": a.time,
                "status": a.status,
                "doctor": a.doctor.name,
            }
            for a in upcoming
        ],
        "history": [
            {
                "id": a.id,
                "date": a.date.isoformat(),
                "time": a.time,
                "status": a.status,
                "doctor": a.doctor.name,
                "diagnosis": a.treatment.diagnosis if a.treatment else None,
                "prescription": a.treatment.prescription if a.treatment else None,
            }
            for a in history
        ],
    }


@cache.memoize(timeout=120)
def patient_doctors_list(specialization=None):
    query = User.query.join(DoctorProfile).filter(User.role == UserRole.DOCTOR, User.is_active.is_(True))
    if specialization:
        query = query.filter(DoctorProfile.specialization.ilike(f"%{specialization}%"))
    doctors = query.order_by(User.name.asc()).all()

    start = date.today()
    end = start + timedelta(days=7)
    avail_map = {}
    availability = DoctorAvailability.query.filter(
        DoctorAvailability.available_date >= start,
        DoctorAvailability.available_date <= end,
    ).all()
    for a in availability:
        avail_map.setdefault(a.doctor_id, []).append(
            {
                "date": a.available_date.isoformat(),
                "start_time": a.start_time,
                "end_time": a.end_time,
                "is_available": a.is_available,
            }
        )

    return [
        {
            "id": d.id,
            "name": d.name,
            "specialization": d.doctor_profile.specialization,
            "bio": d.doctor_profile.bio,
            "availability": avail_map.get(d.id, []),
        }
        for d in doctors
    ]


@api_bp.get("/patient/doctors")
@auth_required([UserRole.PATIENT])
def patient_doctors():
    specialization = request.args.get("specialization")
    return {"items": patient_doctors_list(specialization)}


@api_bp.post("/patient/appointments")
@auth_required([UserRole.PATIENT])
def patient_book_appointment():
    data = request.get_json(force=True)
    required = ["doctor_id", "date", "time"]
    if any(not data.get(k) for k in required):
        return {"error": "doctor_id, date, time are required"}, 400

    doctor = User.query.filter_by(id=data["doctor_id"], role=UserRole.DOCTOR, is_active=True).first()
    if not doctor:
        return {"error": "Doctor not found"}, 404

    appt_date = parse_date(data["date"])
    if appt_date < date.today():
        return {"error": "Cannot book in past"}, 400
    if not _is_half_hour_time(data["time"]):
        return {"error": "Appointments can only be booked in 30-minute slots (e.g. 10:00, 10:30)"}, 400

    patient_conflict = Appointment.query.filter(
        Appointment.patient_id == g.current_user.id,
        Appointment.date == appt_date,
        Appointment.time == data["time"],
        Appointment.status != AppointmentStatus.CANCELLED,
    ).first()
    if patient_conflict:
        return {"error": "You already have an appointment at this date and time"}, 409

    slot = DoctorAvailability.query.filter_by(doctor_id=doctor.id, available_date=appt_date).first()
    if not slot or not slot.is_available:
        return {"error": "Doctor has no available slot for this date"}, 409
    if not _is_time_within_slot(slot, data["time"]):
        return {
            "error": f"Selected time is outside doctor slot ({slot.start_time} - {slot.end_time})"
        }, 409

    existing = Appointment.query.filter_by(doctor_id=doctor.id, date=appt_date, time=data["time"]).first()
    if existing and existing.status != AppointmentStatus.CANCELLED:
        return {"error": "Doctor already has an appointment in this slot"}, 409

    appt = Appointment(
        patient_id=g.current_user.id,
        doctor_id=doctor.id,
        date=appt_date,
        time=data["time"],
        status=AppointmentStatus.BOOKED,
    )
    db.session.add(appt)
    db.session.add(
        Notification(
            user_id=doctor.id,
            kind="appointment",
            message=f"New appointment booked by {g.current_user.name} for {appt_date.isoformat()} {data['time']}",
        )
    )
    db.session.commit()
    cache.clear()
    return {"message": "Appointment booked", "appointment_id": appt.id}, 201


@api_bp.put("/patient/appointments/<int:appointment_id>")
@auth_required([UserRole.PATIENT])
def patient_reschedule_appointment(appointment_id):
    appt = Appointment.query.filter_by(id=appointment_id, patient_id=g.current_user.id).first_or_404()
    if appt.status == AppointmentStatus.COMPLETED:
        return {"error": "Completed appointment cannot be rescheduled"}, 400

    data = request.get_json(force=True)
    new_date = parse_date(data["date"])
    new_time = data["time"]
    if not _is_half_hour_time(new_time):
        return {"error": "Appointments can only be booked in 30-minute slots (e.g. 10:00, 10:30)"}, 400

    patient_conflict = Appointment.query.filter(
        Appointment.patient_id == g.current_user.id,
        Appointment.date == new_date,
        Appointment.time == new_time,
        Appointment.id != appt.id,
        Appointment.status != AppointmentStatus.CANCELLED,
    ).first()
    if patient_conflict:
        return {"error": "You already have an appointment at this date and time"}, 409

    slot = DoctorAvailability.query.filter_by(doctor_id=appt.doctor_id, available_date=new_date).first()
    if not slot or not slot.is_available:
        return {"error": "Doctor has no available slot for this date"}, 409
    if not _is_time_within_slot(slot, new_time):
        return {
            "error": f"Selected time is outside doctor slot ({slot.start_time} - {slot.end_time})"
        }, 409

    collision = Appointment.query.filter(
        Appointment.doctor_id == appt.doctor_id,
        Appointment.date == new_date,
        Appointment.time == new_time,
        Appointment.id != appt.id,
        Appointment.status != AppointmentStatus.CANCELLED,
    ).first()
    if collision:
        return {"error": "Doctor slot unavailable"}, 409

    appt.date = new_date
    appt.time = new_time
    appt.status = AppointmentStatus.BOOKED
    db.session.commit()
    return {"message": "Appointment rescheduled"}


@api_bp.delete("/patient/appointments/<int:appointment_id>")
@auth_required([UserRole.PATIENT])
def patient_cancel_appointment(appointment_id):
    appt = Appointment.query.filter_by(id=appointment_id, patient_id=g.current_user.id).first_or_404()
    if appt.status == AppointmentStatus.COMPLETED:
        return {"error": "Cannot cancel completed appointment"}, 400
    appt.status = AppointmentStatus.CANCELLED
    db.session.commit()
    return {"message": "Appointment cancelled"}


@api_bp.get("/patient/history")
@auth_required([UserRole.PATIENT])
def patient_history():
    items = (
        Appointment.query.filter_by(patient_id=g.current_user.id)
        .filter(Appointment.status == AppointmentStatus.COMPLETED)
        .order_by(Appointment.date.desc())
        .all()
    )
    return {
        "items": [
            {
                "appointment_id": a.id,
                "doctor": a.doctor.name,
                "date": a.date.isoformat(),
                "diagnosis": a.treatment.diagnosis if a.treatment else None,
                "prescription": a.treatment.prescription if a.treatment else None,
                "notes": a.treatment.notes if a.treatment else None,
                "next_visit_date": a.treatment.next_visit_date.isoformat() if a.treatment and a.treatment.next_visit_date else None,
            }
            for a in items
        ]
    }


@api_bp.put("/patient/profile")
@auth_required([UserRole.PATIENT])
def patient_update_profile():
    data = request.get_json(force=True)
    user = g.current_user
    user.name = data.get("name", user.name)
    user.email = data.get("email", user.email)
    user.phone = data.get("phone", user.phone)
    db.session.commit()
    return {"message": "Profile updated", "user": user_payload(user)}
