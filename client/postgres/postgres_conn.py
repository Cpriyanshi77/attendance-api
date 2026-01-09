import psycopg2
import os
from collections import OrderedDict
from typing import List
import yaml
import psycopg2
import psycopg2.extras
from models.message import CustomMessage, HealthMessage
from models.user_info import EmployeeInfo
from client.redis import MiddlewareSDKFacade

CONFIG_FILE = os.getenv('CONFIG_FILE', 'config.yaml')

class CorePostgresClient:
    """Class for defining the interface for Postgres Client"""
    def __init__(self):
        with open(CONFIG_FILE, 'r', encoding="utf-8") as config_file:
            yaml_values = yaml.load(config_file, Loader=yaml.FullLoader)
        self.client = psycopg2.connect(
            database=yaml_values['postgres']['database'],
            host=yaml_values['postgres']['host'],
            user=yaml_values['postgres']['user'],
            password=yaml_values['postgres']['password'],
            port=yaml_values['postgres']['port']
        )
        self.client.autocommit = False  # manual transaction handling

    def _record_to_domain_model(self, response):
        return EmployeeInfo(
            id=response.get("id"),
            name=response.get("name"),
            status=response.get("status"),
            date=response.get("date")
        )

    def read_employee_attendance(self, id_value) -> EmployeeInfo:
        """Read a particular employee attendance record"""
        cursor = self.client.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute("SELECT id, name, status, date FROM records WHERE id = %s", (id_value,))
            response = cursor.fetchone()
            return self._record_to_domain_model(OrderedDict(response)) if response else None
        finally:
            cursor.close()

    def read_all_employee_attendance(self) -> List[EmployeeInfo]:
        """Read all employee attendance records"""
        cursor = self.client.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute("SELECT id, name, status, date FROM records ORDER BY id DESC")
            return [self._record_to_domain_model(row) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def create_employee_attendance(self, id, name, status, date):
        """Create a new employee attendance record"""
        cursor = self.client.cursor()
        try:
            insert_query = """INSERT INTO records (id, name, status, date) VALUES (%s,%s,%s,%s)"""
            cursor.execute(insert_query, (id, name, status, date))
            self.client.commit()
            return CustomMessage(
                message=f"Successfully created the record for employee id: {id}"
            ), 201
        except psycopg2.errors.UniqueViolation:
            self.client.rollback()
            return CustomMessage(
                message=f"Record with id {id} already exists"
            ), 400
        except Exception as e:
            self.client.rollback()
            return CustomMessage(
                message=f"Unexpected error: {str(e)}"
            ), 500
        finally:
            cursor.close()

    def attendance_detail_health(self):
        """Detailed health check for Attendance API"""
        cursor = self.client.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute("SELECT 1")
            return HealthMessage(
                message="Attendance API is running fine and ready to serve requests",
                postgresql="up",
                redis=MiddlewareSDKFacade.cache.redis_status(),
                status="up",
            ), 200
        except Exception:
            self.client.rollback()
            return HealthMessage(
                message="Attendance API is not healthy, please check logs",
                postgresql="down",
                redis=MiddlewareSDKFacade.cache.redis_status(),
                status="down",
            ), 500
        finally:
            cursor.close()

    def attendance_health(self):
        """Simple health check for Attendance API"""
        cursor = self.client.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute("SELECT 1")
            return CustomMessage(
                message="Attendance API is running fine and ready to serve requests",
            ), 200
        except Exception:
            self.client.rollback()
            return CustomMessage(
                message="Attendance API is not healthy, please check logs",
            ), 500
        finally:
            cursor.close()
