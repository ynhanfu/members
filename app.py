import os
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
import motor.motor_asyncio
import uvicorn

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client.members


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class MemberModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    names: str = Field(...)
    nickname: str = Field(...)
    phone: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "names": "Jane Doe",
                "nickname": "Peter Pan",
                "phone": "15887218868",
            }
        }


class UpdateMemberModel(BaseModel):
    names: Optional[str]
    nickname: Optional[str]
    phone: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "names": "Jane Doe",
                "nickname": "Peter Pan",
                "phone": "15887218868",
            }
        }


@app.post("/", response_description="Add new member", response_model=MemberModel)
async def create_member(member: MemberModel = Body(...)):
    member = jsonable_encoder(member)
    new_member = await db["members"].insert_one(member)
    created_member = await db["members"].find_one({"_id": new_member.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_member)


@app.get(
    "/", response_description="List all members", response_model=List[MemberModel]
)
async def list_members():
    members = await db["members"].find().to_list(1000)
    return members


@app.get(
    "/{id}", response_description="Get a single member", response_model=MemberModel
)
async def show_member(id: str):
    if (member := await db["members"].find_one({"_id": id})) is not None:
        return member

    raise HTTPException(status_code=404, detail=f"Member {id} not found")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
