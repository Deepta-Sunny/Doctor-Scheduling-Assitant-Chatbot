"""
Pydantic models for API responses.
Ensures consistent, validated response structures.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class PDFProcessResponse(BaseModel):
    """Response from PDF processing operation"""
    success: bool = Field(..., description="Whether processing succeeded")
    filename: str = Field(..., description="Name of processed file")
    total_pages: Optional[int] = Field(None, description="Number of pages in PDF")
    total_chunks: Optional[int] = Field(None, description="Number of chunks created")
    message: str = Field(..., description="Success or error message")
    error: Optional[str] = Field(None, description="Error details if failed")

class SearchResult(BaseModel):
    """Result from vector search operation"""
    documents: List[str] = Field(default_factory=list, description="Retrieved documents")
    metadatas: List[Dict[str, Any]] = Field(default_factory=list, description="Document metadata")
    distances: Optional[List[float]] = Field(None, description="Similarity distances")

class CollectionStats(BaseModel):
    """Statistics about a vector collection"""
    total_chunks: int = Field(..., description="Total number of chunks in collection")
    collection_name: str = Field(..., description="Name of the collection")

class DoctorInfo(BaseModel):
    """Structured doctor information"""
    name: str = Field(..., description="Doctor's full name")
    specialty: str = Field(..., description="Medical specialty")
    experience_years: int = Field(..., description="Years of experience")
    consultation_fees: float = Field(..., description="Consultation fee in rupees")
    hospital_name: str = Field(..., description="Hospital name")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    address: str = Field(..., description="Full address")
    pincode: str = Field(..., description="Postal code")
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Rajesh Kumar",
                "specialty": "Cardiology",
                "experience_years": 15,
                "consultation_fees": 1000.0,
                "hospital_name": "Apollo Hospital",
                "city": "Mumbai",
                "state": "Maharashtra",
                "address": "Andheri West",
                "pincode": "400053"
            }
        }

class DoctorSearchResponse(BaseModel):
    """Response from doctor search"""
    success: bool = Field(..., description="Whether search succeeded")
    doctors: List[DoctorInfo] = Field(default_factory=list, description="List of doctors found")
    specialty: str = Field(..., description="Specialty searched for")
    city: Optional[str] = Field(None, description="City filter applied")
    count: int = Field(..., description="Number of doctors found")
    message: str = Field(..., description="Human-readable message")
