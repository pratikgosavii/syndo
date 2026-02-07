"""
Appointment push notifications: different messages to patient (customer) and dentist
based on appointment creation and status changes.

Usage (when you have an Appointment model with patient_user, dentist_user, status, scheduled_date):

  from customer.appointment_notifications import send_appointment_status_notifications

  # On appointment creation (notify dentist only):
  send_appointment_status_notifications(
      patient_user=appointment.patient_user,
      dentist_user=appointment.dentist_user,
      status='received',
      appointment_id=appointment.id,
  )

  # On status change (notify both as per status):
  send_appointment_status_notifications(
      patient_user=appointment.patient_user,
      dentist_user=appointment.dentist_user,
      status=appointment.status,  # accepted, rescheduled, next_appointment, rescheduled_by_patient, completed
      appointment_id=appointment.id,
      appointment_date=appointment.scheduled_date,
      patient_name=appointment.patient_user.get_full_name() or appointment.patient_user.mobile,
  )
"""

import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


def _format_appointment_date(appointment_date):
    """Return a display string for appointment_date (datetime, date, or str)."""
    if appointment_date is None:
        return None
    if isinstance(appointment_date, (datetime, date)):
        return appointment_date.strftime("%d %b %Y")
    return str(appointment_date)

# Patient (customer) messages by status
APPOINTMENT_PATIENT_MESSAGES = {
    'accepted': ('Appointment Accepted', 'Your appointment has been accepted'),
    'rescheduled': ('Appointment Rescheduled', 'Your appointment has been Rescheduled'),
    'next_appointment': ('Next Appointment', 'Your Next appointment has been booked for day {date}'),
    'rescheduled_by_patient': ('Appointment Rescheduled', 'you have successfully rescheduled your appointment'),
    'completed': ('Appointment Completed', 'Congratulations your appointment has been successfully completed'),
}

# Dentist messages by status
APPOINTMENT_DENTIST_MESSAGES = {
    'received': ('New Appointment', 'You have got a new appointment'),
    'rescheduled': ('Appointment Rescheduled', 'Your appointment has been Rescheduled'),
    'next_appointment': ('Next Appointment', 'Your Next appointment has been booked for day {date}'),
    'rescheduled_by_patient': ('Appointment Rescheduled', '{patient_name} has rescheduled your appointment'),
    'completed': ('Appointment Completed', 'Congratulations your appointment with {patient_name} has successfully completed'),
}


def _send_push_to_user(user, title, body, data=None):
    """Send FCM push to a single user. Returns True if sent, False otherwise."""
    if not user:
        return False
    try:
        from firebase_admin import messaging
        from users.models import DeviceToken
    except ImportError:
        logger.warning("Firebase/DeviceToken not available for appointment notification")
        return False

    try:
        device_token_obj = DeviceToken.objects.get(user=user)
        if not device_token_obj.token or not device_token_obj.token.strip():
            logger.warning(f"No device token for user {user.id}, skipping appointment push")
            return False
        token = device_token_obj.token.strip()
    except DeviceToken.DoesNotExist:
        logger.warning(f"No device token for user {user.id}, skipping appointment push")
        return False

    payload = dict(data) if data else {}
    payload = {k: str(v) for k, v in payload.items()}

    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=payload,
            token=token,
        )
        messaging.send(message)
        logger.info(f"Appointment push sent to user {user.id}: {title}")
        return True
    except Exception as e:
        logger.error(f"Failed to send appointment push to user {user.id}: {e}")
        if "Requested entity was not found" in str(e):
            try:
                DeviceToken.objects.filter(user=user).delete()
                logger.warning(f"Removed invalid device token for user {user.id}")
            except Exception:
                pass
        return False


def send_appointment_notification_to_patient(patient_user, status, appointment_date=None):
    """
    Send push notification to patient (customer) for the given status.
    Status: accepted, rescheduled, next_appointment, rescheduled_by_patient, completed.
    appointment_date: datetime, date, or str; used for next_appointment body.
    """
    msg = APPOINTMENT_PATIENT_MESSAGES.get(status)
    if not msg:
        logger.info(f"No patient message for appointment status: {status}")
        return False
    title, body = msg
    if status == 'next_appointment' and appointment_date is not None:
        body = body.format(date=_format_appointment_date(appointment_date))
    return _send_push_to_user(
        patient_user,
        title,
        body,
        data={'type': 'appointment_status', 'status': status},
    )


def send_appointment_notification_to_dentist(dentist_user, status, appointment_date=None, patient_name=None):
    """
    Send push notification to dentist for the given status.
    Status: received, rescheduled, next_appointment, rescheduled_by_patient, completed.
    For rescheduled_by_patient and completed, patient_name is used in the body.
    """
    msg = APPOINTMENT_DENTIST_MESSAGES.get(status)
    if not msg:
        logger.info(f"No dentist message for appointment status: {status}")
        return False
    title, body = msg
    if status == 'next_appointment' and appointment_date is not None:
        body = body.format(date=_format_appointment_date(appointment_date))
    if status in ('rescheduled_by_patient', 'completed') and patient_name is not None:
        body = body.format(patient_name=patient_name)
    return _send_push_to_user(
        dentist_user,
        title,
        body,
        data={'type': 'appointment_status', 'status': status},
    )


def send_appointment_status_notifications(
    patient_user,
    dentist_user,
    status,
    appointment_id=None,
    appointment_date=None,
    patient_name=None,
):
    """
    Send push notifications to patient and/or dentist based on appointment status.
    Call this on appointment creation and on every status change.

    - On creation: pass status='received' → only dentist is notified.
    - On status change: pass the new status → both get their message where applicable.

    Args:
        patient_user: User model for the patient (can be None for status='received').
        dentist_user: User model for the dentist.
        status: One of received, accepted, rescheduled, next_appointment, rescheduled_by_patient, completed.
        appointment_id: Optional; included in data payload.
        appointment_date: Optional; datetime/date/str, used for next_appointment body (e.g. "15 Jan 2026").
        patient_name: Optional; used in dentist body for rescheduled_by_patient and completed.
    """
    appointment_date = _format_appointment_date(appointment_date) if appointment_date is not None else None
    data = {}
    if appointment_id is not None:
        data['appointment_id'] = str(appointment_id)

    sent_patient = False
    sent_dentist = False

    # Notify patient (except for 'received', which is dentist-only)
    if status != 'received' and patient_user and status in APPOINTMENT_PATIENT_MESSAGES:
        sent_patient = send_appointment_notification_to_patient(
            patient_user, status, appointment_date=appointment_date
        )

    # Notify dentist
    if dentist_user and status in APPOINTMENT_DENTIST_MESSAGES:
        sent_dentist = send_appointment_notification_to_dentist(
            dentist_user, status,
            appointment_date=appointment_date,
            patient_name=patient_name,
        )

    return sent_patient, sent_dentist
