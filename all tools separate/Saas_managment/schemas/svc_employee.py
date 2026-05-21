"""Pydantic schema for employee records."""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


class Employee(BaseModel):
    employee_id: str
    email: str
    department: str
    job_level: str
    region: str
    is_active: bool
    hire_date: date
    exit_date: Optional[date] = None
    exit_type: Optional[str] = None
    manager_id: Optional[str] = None
    employee_status: Optional[str] = None

