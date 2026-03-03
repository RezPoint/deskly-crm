from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_serializer, condecimal

Money = condecimal(max_digits=12, decimal_places=2)

class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("*", when_used="json", check_fields=False)
    def _serialize_decimal(self, value):
        if isinstance(value, Decimal):
            return float(value)
        return value
