from typing import Optional
from pydantic import BaseModel, EmailStr

class ContactForm(BaseModel):
    name: str
    email: EmailStr


# --- Prototype Models ---

class InitialFilterForm(BaseModel):
    is_manufacturing: bool
    consumes_significant_energy: bool
    tracks_env_metrics: bool
    measures_emissions: bool
    has_sustainability_goals: bool
    applied_for_esg_loan: bool
    has_employee_policies: bool

class GreenLoanIntake(BaseModel):
    annual_electricity_kwh: float
    annual_fuel_litres: float
    water_consumption_litres: float
    waste_generated_kg_month: float
    renewable_energy_pct: float
    efficiency_equipment: Optional[str] = None
    industry_code: Optional[str] = None

class SLLIntake(BaseModel):
    turnover_last_3_years: str 
    target_improvement_goals: str
    num_employees: int
    workforce_diversity_stats: Optional[str] = None
    safety_incident_count: int
    training_programs: Optional[str] = None
    governance_policies: Optional[str] = None

class OtherIntake(BaseModel):
    business_info: str
    existing_docs: Optional[str] = None
    interest_areas: Optional[str] = None

