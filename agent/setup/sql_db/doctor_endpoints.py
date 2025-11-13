from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from setup.sql_db.database_setup import get_db, Doctor, User

router = APIRouter(prefix="/api/doctors", tags=["doctors"])


# Response Model
class DoctorSearchResponse(BaseModel):
    doctor_name: str
    years_of_experience: int
    consultation_fees: float
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    hospital_name: Optional[str] = None
    speciality: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/search", response_model=List[DoctorSearchResponse])
async def search_doctors(
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    city: Optional[str] = Query(None, description="Filter by city"),
    db: Session = Depends(get_db)
):
    """
    Search for doctors by specialty and/or city.
    
    Returns: doctor name, years of experience, consultation fees, 
    address, city, state, pincode, hospital name, and speciality.
    """
    try:
        # Query with JOIN between Users and Doctors tables
        query = db.query(
            User.Name.label("doctor_name"),
            Doctor.YearsOfExperience.label("years_of_experience"),
            Doctor.ConsultationFees.label("consultation_fees"),
            Doctor.Address.label("address"),
            Doctor.City.label("city"),
            Doctor.State.label("state"),
            Doctor.Pincode.label("pincode"),
            Doctor.HospitalName.label("hospital_name"),
            Doctor.Speciality.label("speciality")
        ).join(
            Doctor, User.UserId == Doctor.UserId
        ).filter(
            User.IsDoctor == True
        )
        
        # Apply filters if provided
        if specialty:
            query = query.filter(Doctor.Speciality.ilike(f"%{specialty}%"))
        
        if city:
            query = query.filter(Doctor.City.ilike(f"%{city}%"))
        
        # Execute query
        results = query.all()
        
        if not results:
            return []
        
        # Convert to response format
        doctors = []
        for result in results:
            doctors.append(DoctorSearchResponse(
                doctor_name=result.doctor_name,
                years_of_experience=result.years_of_experience,
                consultation_fees=float(result.consultation_fees),
                address=result.address,
                city=result.city,
                state=result.state,
                pincode=result.pincode,
                hospital_name=result.hospital_name,
                speciality=result.speciality
            ))
        
        return doctors
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")