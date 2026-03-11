import os
from datetime import date, datetime, timedelta

from .extensions import celery, db
from .models import Appointment, AppointmentStatus, Notification, User, UserRole
from .utils import push_webhook_message


@celery.task(name="app.tasks.send_daily_reminders")
def send_daily_reminders():
    today = date.today()
    appointments = Appointment.query.filter_by(date=today, status=AppointmentStatus.BOOKED).all()
    sent = 0
    for appt in appointments:
        msg = f"Reminder: You have a hospital appointment today at {appt.time} with Dr. {appt.doctor.name}."
        db.session.add(Notification(user_id=appt.patient_id, kind="reminder", message=msg))
        push_webhook_message(msg)
        sent += 1
    db.session.commit()
    return {"sent": sent, "date": today.isoformat()}


@celery.task(name="app.tasks.send_monthly_doctor_reports")
def send_monthly_doctor_reports():
    today = date.today()
    month_start = today.replace(day=1)
    previous_month_end = month_start - timedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1)

    doctors = User.query.filter_by(role=UserRole.DOCTOR, is_active=True).all()
    reports = []

    out_dir = os.path.join(os.path.dirname(__file__), "..", "exports", "reports")
    os.makedirs(out_dir, exist_ok=True)

    for doctor in doctors:
        appts = (
            Appointment.query.filter(
                Appointment.doctor_id == doctor.id,
                Appointment.date >= previous_month_start,
                Appointment.date <= previous_month_end,
                Appointment.status == AppointmentStatus.COMPLETED,
            )
            .order_by(Appointment.date.asc())
            .all()
        )

        html_rows = "".join(
            [
                f"<tr><td>{a.date.isoformat()}</td><td>{a.patient.name}</td><td>{a.treatment.diagnosis if a.treatment else ''}</td><td>{a.treatment.prescription if a.treatment else ''}</td></tr>"
                for a in appts
            ]
        )

        html = f"""
        <html>
        <body>
            <h2>Monthly Activity Report - Dr. {doctor.name}</h2>
            <p>Period: {previous_month_start.isoformat()} to {previous_month_end.isoformat()}</p>
            <table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">
                <thead><tr><th>Date</th><th>Patient</th><th>Diagnosis</th><th>Prescription</th></tr></thead>
                <tbody>{html_rows}</tbody>
            </table>
        </body>
        </html>
        """

        report_path = os.path.join(out_dir, f"doctor_{doctor.id}_{previous_month_start.strftime('%Y_%m')}.html")
        with open(report_path, "w", encoding="utf-8") as fp:
            fp.write(html)
        reports.append(report_path)

        db.session.add(
            Notification(
                user_id=doctor.id,
                kind="monthly_report",
                message=f"Monthly report generated: {os.path.abspath(report_path)}",
            )
        )

    db.session.commit()
    return {"reports_generated": len(reports), "files": [os.path.abspath(x) for x in reports]}
