from pydantic import BaseModel

class VendorRequest(BaseModel):
    company_name: str
    services: str
    domain: str = ""
    ticker: str = ""