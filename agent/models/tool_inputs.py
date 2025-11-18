"""
Pydantic models for tool input validation.
Ensures tools receive valid, clean parameters and protects against malicious input.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class DoctorSearchInput(BaseModel):
    """
    Validated input for doctor search tool.
    Ensures specialty and city are valid before database query.
    """
    specialty_name: str = Field(
        ..., 
        description="Medical specialty - must match predefined list"
    )
    city: Optional[str] = Field(
        None,
        description="City name for filtering doctors",
        min_length=2,
        max_length=100
    )
    
    @field_validator('specialty_name')
    @classmethod
    def validate_specialty(cls, v: str) -> str:
        """Ensure specialty is from allowed list and safe"""
        if not v or len(v.strip()) == 0:
            raise ValueError("Specialty name cannot be empty")
        
        v = v.strip()
        if not re.match(r'^[a-zA-Z\s-]+$', v):
            raise ValueError("Specialty name contains invalid characters")
        
        ALLOWED_SPECIALTIES = {
            "Dermatology", "Cardiology", "Neurology", "Orthopedics",
            "Pediatrics", "Gynecology", "Ophthalmology", "Psychiatry",
            "ENT", "Urology", "Oncology", "Gastroenterology",
            "Pulmonology", "Nephrology", "Endocrinology"
        }
        
        for specialty in ALLOWED_SPECIALTIES:
            if v.lower() == specialty.lower():
                return specialty
        
        raise ValueError(
            f"Invalid specialty '{v}'. Available: {', '.join(sorted(ALLOWED_SPECIALTIES))}"
        )
    
    @field_validator('city')
    @classmethod
    def clean_city(cls, v: Optional[str]) -> Optional[str]:
        """Clean and format city name, remove special characters and SQL injection attempts"""
        if v:
            cleaned = v.strip()
            if not cleaned:
                return None
            
            sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION', '--', ';', '/*', '*/', 'EXEC']
            if any(keyword in cleaned.upper() for keyword in sql_keywords):
                raise ValueError("Invalid city name format")
            
            cleaned = ''.join(char for char in cleaned if char.isalnum() or char in ' -,.')
            
            if len(cleaned) > 50:
                cleaned = cleaned[:50]
            
            return cleaned.title()
        return v

class FAQSearchInput(BaseModel):
    """
    Validated input for FAQ search tool.
    Ensures query is valid and n_results is within limits.
    """
    query: str = Field(
        ...,
        description="User's question to search in FAQ",
        min_length=3,
        max_length=500
    )
    n_results: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of FAQ results to return (1-10)"
    )
    
    @field_validator('query')
    @classmethod
    def clean_query(cls, v: str) -> str:
        """Clean and validate query string, prevent injection attacks"""
        cleaned = v.strip()
        
        if len(cleaned) < 3:
            raise ValueError("Query must be at least 3 characters long")
        
        cleaned = ' '.join(cleaned.split())
        
        dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onclick=']
        if any(pattern in cleaned.lower() for pattern in dangerous_patterns):
            raise ValueError("Query contains invalid content")
        
        return cleaned
