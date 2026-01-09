"""
Module for all the application routes and their respective handlers
- create_record
- read_record
- read_all_record
- get_detail_healthcheck
- get_healthcheck
"""

# pylint: disable=import-error,invalid-name,redefined-builtin
from flask import Blueprint, jsonify, request
from voluptuous import Schema, Required
from client.postgres import DatabaseSDKFacade
from utils.validator import data_validator
from router.cache import cache
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime, format_datetime

route = Blueprint("attendance", __name__)

@route.route("/attendance/create", methods=["POST"])
@data_validator(
    Schema(
        {
            Required("id"): str,
            Required("name"): str,
            Required("status"): str,
            Required("date"):str,
        }
    )
)
def create_record(
        id: str,
        name: str,
        status: str,
        date: str,
):
    """
    Function for creating the record in the database
    ...
    """
    # Normalize incoming date to RFC format expected by the DB/API layer
    normalized_date = None
    s = (date or "").strip()
    if not s:
        return jsonify({"message": "Invalid date format", "detail": "empty date"}), 400

    # 1) Try ISO date YYYY-MM-DD (most common from UI)
    try:
        if len(s) == 10 and s.count("-") == 2:
            # treat as midnight UTC
            dt = datetime.fromisoformat(s + "T00:00:00")
            dt = dt.replace(tzinfo=timezone.utc)
            normalized_date = format_datetime(dt)
    except Exception:
        normalized_date = None

    # 2) If not yet parsed, try ISO datetime variants (with time)
    if normalized_date is None:
        try:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            normalized_date = format_datetime(dt)
        except Exception:
            normalized_date = None

    # 3) If still not parsed, try RFC-like parsing
    if normalized_date is None:
        try:
            dt = parsedate_to_datetime(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            normalized_date = format_datetime(dt)
        except Exception:
            normalized_date = None

    if normalized_date is None:
        return jsonify({"message": "Invalid date format", "detail": f"Unrecognized date: {date}"}), 400

    # call DB using normalized RFC date string
    # At this point `dt` is the parsed datetime object used above.
    # Convert to ISO date string (YYYY-MM-DD) for storage
    try:
        # ensure dt exists: if you parsed using the earlier logic, dt is set
        iso_date = dt.date().isoformat()
    except NameError:
        # fallback: try to parse s to get a datetime
        try:
            parsed = datetime.fromisoformat(s) if len(s) == 10 else parsedate_to_datetime(s)
            iso_date = parsed.date().isoformat()
        except Exception:
            return jsonify({"message": "Invalid date format", "detail": s}), 400

    record = DatabaseSDKFacade.database.create_employee_attendance(id, name, status, iso_date)
    return jsonify(record)


@route.route("/attendance/search", methods=["GET"])
@cache.cached(timeout=20)
def read_record():
    """
    Function for reading the record from the database
    ---
    consumes:
      - application/json
    description: Read record of employee attendance
    produces:
      - application/json
    parameters:
    - description: User ID
      in: query
      name: id
      required: true
      type: string
    definitions:
      EmployeeInfo:
        properties:
          id:
            type: string
          name:
            type: string
          status:
            type: string
          date:
            type: string
        type: object
    responses:
      200:
        description: OK
        schema:
          $ref: '#/definitions/EmployeeInfo'
    summary: ReadRecord API is for getting particular attendance record
    tags:
      - attendance
    """
    args = request.args
    id = args.get("id", default="", type=str)
    if id != "":
        record = DatabaseSDKFacade.database.read_employee_attendance(id)
        return jsonify(record)
    return jsonify({"message": f"Unable to process request, please check query params {id}"}), 400

@route.route("/attendance/search/all", methods=["GET"])
@cache.cached(timeout=20)
def read_all_record():
    """
    Function for reading all the record from the database
    ---
    consumes:
      - application/json
    description: Read record of all employee attendance records
    produces:
      - application/json
    definitions:
      EmployeeInfo:
        properties:
          id:
            type: string
          name:
            type: string
          status:
            type: string
          date:
            type: string
        type: object
    responses:
      200:
        description: OK
        schema:
          $ref: '#/definitions/EmployeeInfo'
          type: array
    summary: ReadRecord API is for getting all attendance record
    tags:
      - attendance
    """
    records = DatabaseSDKFacade.database.read_all_employee_attendance()
    # Convert record['date'] from RFC (if present) to ISO for the UI
    for r in records:
        try:
            dt = parsedate_to_datetime(r.get("date"))
            r["date"] = dt.date().isoformat()
        except Exception:
            # if it's already ISO or unparseable, leave as-is
            pass
    return jsonify(records)


@route.route("/attendance/health/detail", methods=["GET"])
def get_detail_healthcheck():
    """
    Function for getting detailed healthcheck of application
    ---
    consumes:
      - application/json
    description: Do detail healthcheck for attendance API
    produces:
      - application/json
    definitions:
      HealthMessage:
        properties:
          message:
            type: string
          postgresql:
            type: string
          redis:
            type: string
          status:
            type: string
        type: object
    responses:
      200:
        description: OK
        schema:
          $ref: '#/definitions/HealthMessage'
    summary: DetailedHealthCheckAPI is a method to perform detailed healthcheck
    tags:
      - healthcheck
    """
    status, status_code = DatabaseSDKFacade.database.attendance_detail_health()
    return jsonify(status), status_code

@route.route("/attendance/health", methods=["GET"])
def get_healthcheck():
    """
    Function for getting healthcheck of application
    ---
    consumes:
      - application/json
    description: Do healthcheck for attendance API
    produces:
      - application/json
    definitions:
      CustomMessage:
        properties:
          message:
            type: string
        type: object
    responses:
      200:
        description: OK
        schema:
          $ref: '#/definitions/CustomMessage'
    summary: HealthCheckAPI is a method to perform healthcheck of application
    tags:
      - healthcheck
    """
    status, status_code = DatabaseSDKFacade.database.attendance_health()
    return jsonify(status), status_code
