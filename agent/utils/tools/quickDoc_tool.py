from langchain.tools import tool
from agent.setup.sql_db.database_setup import SessionLocal, Doctor, User
from agent.models.tool_inputs import DoctorSearchInput
from pydantic import ValidationError

SPECIALTY_MAP = {
    "Dermatology": 1, "Cardiology": 2, "Neurology": 3, "Orthopedics": 4,
    "Pediatrics": 5, "Gynecology": 6, "Ophthalmology": 7, "Psychiatry": 8,
    "ENT": 9, "Urology": 10, "Oncology": 11, "Gastroenterology": 12,
    "Pulmonology": 13, "Nephrology": 14, "Endocrinology": 15
}

# Reverse mapping: ID -> name
SPECIALTY_ID_TO_NAME = {v: k for k, v in SPECIALTY_MAP.items()}

@tool("get_doctor_details", return_direct=True)
def get_doctor_details(specialty_name: str, city: str = None) -> str:
    """
    Fetch doctor details directly from SQL database.
    Filters by specialty ID (mapped from specialty name) and optionally city.
    Returns formatted doctor information.
    
    Args:
        specialty_name: Medical specialty (e.g., "Cardiology", "Dermatology", "Orthopedics")
        city: City name (e.g., "Mumbai", "Bengaluru", "Delhi")
    
    Returns:
        Formatted string with doctor details including name, experience, fees, hospital, and address.
    """
    # Validate inputs using Pydantic
    try:
        validated_input = DoctorSearchInput(specialty_name=specialty_name, city=city)
        specialty_name = validated_input.specialty_name  # Use canonical form
        city = validated_input.city  # Use cleaned city name
    except ValidationError as e:
        # Extract user-friendly error message
        errors = e.errors()
        if 'specialty_name' in str(errors[0].get('loc', '')):
            # Get available specialties for helpful message
            available = ", ".join(sorted(SPECIALTY_MAP.keys()))
            return f"I don't have doctors for that specialty. Available specialties are: {available}"
        else:
            return f"Please provide a valid city name."
    
    db = SessionLocal()
    
    try:
        # Map specialty name to ID
        specialty_id = SPECIALTY_MAP.get(specialty_name)
        
        if not specialty_id:
            return f"Unknown specialty: {specialty_name}. Please use one of: {', '.join(SPECIALTY_MAP.keys())}"
        
        # Query database with JOIN, filtering by specialty ID
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
            User.IsDoctor == True,
            Doctor.Speciality == specialty_id,
            Doctor.StatusType == 1 
        )
        
        # Add city filter if provided
        if city:
            query = query.filter(Doctor.City.ilike(f"%{city}%"))
        
        # Execute query
        results = query.all()
        
        # Handle no results
        if not results:
            location_text = f" in {city}" if city else ""
            return f"No {specialty_name} doctors found{location_text}. Would you like to try a different city or specialty?"
        
        # Format output
        output = f"Found {len(results)} {specialty_name} doctor(s):\n\n"
        
        for idx, result in enumerate(results, 1):
            # Map specialty ID back to name for display
            specialty_display = SPECIALTY_ID_TO_NAME.get(result.speciality, result.speciality)
            
            output += f"{idx}. Dr. {result.doctor_name}\n"
            output += f"   Specialty: {specialty_display}\n"
            output += f"   Experience: {result.years_of_experience} years\n"
            output += f"   Consultation Fee: ₹{result.consultation_fees}\n"
            output += f"   Hospital: {result.hospital_name}\n"
            output += f"   Location: {result.city}, {result.state}\n"
            output += f"   Address: {result.address}, {result.pincode}\n\n"
        
        return output.strip()
    
    except Exception as e:
        return f"Error searching for doctors: {str(e)}"
    
    finally:
        db.close()


# Export as list
quickDoc_tools = [get_doctor_details]