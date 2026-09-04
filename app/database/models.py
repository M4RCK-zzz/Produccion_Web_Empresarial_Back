# backend/app/database/models.py
from sqlalchemy import Column, BigInteger, String, Boolean, Text, Numeric, Date, ForeignKey, Integer, JSON, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from app.database.connection import Base

class ClienteModel(Base):
    __tablename__ = "clientes"
    __table_args__ = {'extend_existing': True} # <-- Permite redefinir la tabla sin lanzar la excepción

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    telefono = Column(String(30))
    empresa = Column(String(100))
    activo = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class ComentarioModel(Base):
    __tablename__ = "comentarios"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id", ondelete="SET NULL"))
    contenido = Column(Text, nullable=False)
    canal = Column(String(30), default="web")
    estado = Column(String(30), default="pendiente")
    categoria = Column(String(50))
    fecha = Column(TIMESTAMP, server_default=func.now())
    procesado = Column(Boolean, default=False)

class AnalisisNlpModel(Base):
    __tablename__ = "analisis_nlp"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    comentario_id = Column(BigInteger, ForeignKey("comentarios.id", ondelete="CASCADE"), nullable=False)
    idioma = Column(String(20), default="es")
    cantidad_palabras = Column(Integer, default=0)
    palabras_limpias = Column(JSON)
    palabras_frecuentes = Column(JSON)
    categoria_detectada = Column(String(100))
    confianza = Column(Numeric(5, 4))
    fecha_analisis = Column(TIMESTAMP, server_default=func.now())

class TiemposAtencionModel(Base):
    __tablename__ = "tiempos_atencion"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id", ondelete="SET NULL"))
    comentario_id = Column(BigInteger, ForeignKey("comentarios.id", ondelete="SET NULL"))
    tiempo_minutos = Column(Numeric(10, 2), nullable=False)
    fecha = Column(Date, server_default=func.current_date())
    operador = Column(String(150))
    created_at = Column(TIMESTAMP, server_default=func.now())

class MetricasEstadisticasModel(Base):
    __tablename__ = "metricas_estadisticas"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    cantidad_registros = Column(Integer, nullable=False)
    media = Column(Numeric(12, 4))
    mediana = Column(Numeric(12, 4))
    desviacion_estandar = Column(Numeric(12, 4))
    minimo = Column(Numeric(12, 4))
    maximo = Column(Numeric(12, 4))
    percentil_25 = Column(Numeric(12, 4))
    percentil_75 = Column(Numeric(12, 4))
    created_at = Column(TIMESTAMP, server_default=func.now())