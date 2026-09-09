from sqlalchemy import Column, BigInteger, Integer, String, Boolean, Text, Numeric, Date, ForeignKey, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from app.database.connection import Base


class ClienteModel(Base):
    __tablename__ = "clientes"
    __table_args__ = {'extend_existing': True}

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
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=True)
    texto = Column(Text, nullable=False)
    fecha = Column(TIMESTAMP, server_default=func.now())
    procesado = Column(Boolean, default=False)


class AnalisisNlpModel(Base):
    __tablename__ = "analisis_nlp"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    comentario_id = Column(BigInteger, ForeignKey("comentarios.id"), nullable=False)
    sentimiento = Column(String(50))
    confianza = Column(Numeric(5, 4))
    palabras_clave = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())


class TiempoAtencionModel(Base):
    __tablename__ = "tiempos_atencion"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=True)
    tiempo_minutos = Column(Numeric(10, 2), nullable=False)
    fecha = Column(Date, server_default=func.current_date())


class MetricasEstadisticasModel(Base):
    __tablename__ = "metricas_estadisticas"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    cantidad_registros = Column(Integer, nullable=False)
    media = Column(Numeric(10, 2))
    mediana = Column(Numeric(10, 2))
    desviacion_estandar = Column(Numeric(10, 2))
    minimo = Column(Numeric(10, 2))
    maximo = Column(Numeric(10, 2))
    percentil_25 = Column(Numeric(10, 2))
    percentil_75 = Column(Numeric(10, 2))
    created_at = Column(TIMESTAMP, server_default=func.now())


class OptimizacionModel(Base):
    __tablename__ = "optimizaciones"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    estado = Column(String(50), default="pendiente")
    costo_inicial = Column(Numeric(12, 2))
    costo_optimizado = Column(Numeric(12, 2))
    resultado = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())