import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, BigInteger, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from urllib.parse import quote_plus

load_dotenv()

DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Using pymssql instead of pyodbc (no ODBC driver required)
connection_string = (
    f"mssql+pymssql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_SERVER}/{DB_NAME}"
)

engine = create_engine(connection_string, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "Users"
    __table_args__ = {'schema': 'dbo'}
    
    UserId = Column(BigInteger, primary_key=True, index=True)
    EmailId = Column(String(255), nullable=False)
    Name = Column(String(255), nullable=False)
    Gender = Column(String(1))
    DateOfBirth = Column(DateTime)
    PhoneNo = Column(String(255))
    ProfileImage = Column(String(255))
    IsPatient = Column(Boolean, nullable=False)
    IsAdmin = Column(Boolean, nullable=False)
    IsDoctor = Column(Boolean, nullable=False)
    CreatedBy = Column(String(255))
    CreatedOn = Column(DateTime)
    UpdatedBy = Column(String(255))
    UpdatedOn = Column(DateTime)
    
    doctor = relationship("Doctor", back_populates="user", uselist=False)


class Doctor(Base):
    __tablename__ = "Doctors"
    __table_args__ = {'schema': 'dbo'}
    
    UserId = Column(BigInteger, ForeignKey('dbo.Users.UserId'), primary_key=True, index=True)
    YearsOfExperience = Column(Integer, nullable=False)
    ConsultationFees = Column(Float, nullable=False)
    CertificateLink = Column(String(255))
    StatusType = Column(Integer)
    Address = Column(String(255))
    City = Column(String(255))
    State = Column(String(255))
    Pincode = Column(String(255))
    HospitalName = Column(String(255))
    Speciality = Column(String(255))
    CreatedBy = Column(String(255))
    CreatedOn = Column(DateTime)
    UpdatedBy = Column(String(255))
    UpdatedOn = Column(DateTime)
    
    user = relationship("User", back_populates="doctor")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()