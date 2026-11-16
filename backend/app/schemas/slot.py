from datetime import datetime
from pydantic import BaseModel,ConfigDict

class SlotCreate(BaseModel):
    start_time:datetime
    end_time:datetime

class SlotResponse(BaseModel):
    id:int
    doctor_id:int
    start_time:datetime
    end_time:datetime

    model_config=ConfigDict(from_attributes=True)
    
