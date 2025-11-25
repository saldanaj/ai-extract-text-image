"""Pydantic models for structured data extraction from lead images"""

from pydantic import BaseModel, Field
from typing import Optional


class ContactInfo(BaseModel):
    """Structured lead/contact information extracted from image"""

    # Primary contact details
    full_name: Optional[str] = Field(
        None,
        description="Full name of the contact"
    )
    company_name: Optional[str] = Field(
        None,
        description="Company or organization name"
    )
    job_title: Optional[str] = Field(
        None,
        description="Job title or position"
    )

    # Contact methods
    phone_number: Optional[str] = Field(
        None,
        description="Primary phone number"
    )
    mobile_number: Optional[str] = Field(
        None,
        description="Mobile/cell phone number"
    )
    email: Optional[str] = Field(
        None,
        description="Email address"
    )

    # Address information
    address: Optional[str] = Field(
        None,
        description="Full street address"
    )
    city: Optional[str] = Field(
        None,
        description="City"
    )
    state: Optional[str] = Field(
        None,
        description="State or province"
    )
    zip_code: Optional[str] = Field(
        None,
        description="ZIP or postal code"
    )
    country: Optional[str] = Field(
        None,
        description="Country"
    )

    # Additional fields
    last_contact_date: Optional[str] = Field(
        None,
        description="Last date of contact (typically found in middle of image)"
    )
    website: Optional[str] = Field(
        None,
        description="Company website URL"
    )
    notes: Optional[str] = Field(
        None,
        description="Any additional notes or information"
    )

    # Metadata
    confidence_score: Optional[str] = Field(
        None,
        description="Overall confidence in extraction quality (high/medium/low)"
    )


class ExtractionResult(BaseModel):
    """Complete extraction result wrapper"""
    contact: ContactInfo
    extraction_status: str = Field(
        description="success, partial, or failed"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error details if extraction failed"
    )
