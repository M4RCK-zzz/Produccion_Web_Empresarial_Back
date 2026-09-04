# backend/app/api/clientes.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.connection import get_db
from app.database.models import ClienteModel

router = APIRouter()

# --- Esquemas Pydantic ---
class ClienteBase(BaseModel):
    nombre: str
    email: EmailStr
    telefono: Optional[str] = None
    empresa: Optional[str] = None

    @field_validator("telefono", "empresa", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

class ClienteCreate(ClienteBase):
    pass

class ClienteResponse(ClienteBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Endpoints ---

@router.get("", response_model=List[ClienteResponse])
def obtener_clientes(db: Session = Depends(get_db)):
    try:
        clientes = db.query(ClienteModel).all()
        return clientes if clientes else []
    except Exception as e:
        print(f"Error en GET /api/clientes: {e}")
        return []

@router.post("", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def crear_cliente(cliente_in: ClienteCreate, db: Session = Depends(get_db)):
    # 1. Validar si el email ya existe
    cliente_existente = db.query(ClienteModel).filter(ClienteModel.email == cliente_in.email).first()
    if cliente_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya se encuentra registrado."
        )

    try:
        nuevo_cliente = ClienteModel(**cliente_in.model_dump())
        db.add(nuevo_cliente)
        db.commit()
        db.refresh(nuevo_cliente)
        return nuevo_cliente
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos en la base de datos."
        )
    except Exception as e:
        db.rollback()
        print(f"Error crítico en POST /api/clientes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al crear cliente: {str(e)}"
        )