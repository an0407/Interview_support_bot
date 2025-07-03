from pydantic import BaseModel, Field

class AdminPayload(BaseModel):
    session_id : str = Field(..., examples=['abc@abc.com'])
    query : str = Field(..., examples=["my email is 'abc@abc.com' and I need two volunteers for L1 and L2 for an interview on 01/09/2025"])