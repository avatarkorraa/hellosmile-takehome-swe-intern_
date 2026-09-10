from pydantic import BaseModel


class Context(BaseModel):
    opening_hours: dict
    location: str
    offered_services: list[str]
    contact_info: dict
