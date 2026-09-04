-- database/001_schema.sql
-- Estructura de base de datos para Empresa Inteligente

-- 4. Tabla de usuarios
CREATE TABLE usuarios (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol VARCHAR(30) NOT NULL DEFAULT 'usuario',
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Clientes
CREATE TABLE clientes (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    email VARCHAR(200),
    telefono VARCHAR(50),
    empresa VARCHAR(200),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Categorías de comentarios
CREATE TABLE categorias (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Comentarios de clientes
CREATE TABLE comentarios (
    id BIGSERIAL PRIMARY KEY,
    cliente_id BIGINT REFERENCES clientes(id) ON DELETE SET NULL,
    contenido TEXT NOT NULL,
    canal VARCHAR(30) DEFAULT 'web',
    estado VARCHAR(30) DEFAULT 'pendiente',
    categoria VARCHAR(50),
    fecha TIMESTAMPTZ DEFAULT NOW(),
    procesado BOOLEAN DEFAULT FALSE
);

-- 7. Análisis NLP
CREATE TABLE analisis_nlp (
    id BIGSERIAL PRIMARY KEY,
    comentario_id BIGINT NOT NULL REFERENCES comentarios(id) ON DELETE CASCADE,
    idioma VARCHAR(20) DEFAULT 'es',
    cantidad_palabras INTEGER DEFAULT 0,
    palabras_limpias JSONB,
    palabras_frecuentes JSONB,
    categoria_detectada VARCHAR(100),
    confianza NUMERIC(5,4),
    fecha_analisis TIMESTAMPTZ DEFAULT NOW()
);

-- 9. Tiempos de atención
CREATE TABLE tiempos_atencion (
    id BIGSERIAL PRIMARY KEY,
    cliente_id BIGINT REFERENCES clientes(id) ON DELETE SET NULL,
    comentario_id BIGINT REFERENCES comentarios(id) ON DELETE SET NULL,
    tiempo_minutos NUMERIC(10,2) NOT NULL,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    operador VARCHAR(150),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. Métricas estadísticas
CREATE TABLE metricas_estadisticas (
    id BIGSERIAL PRIMARY KEY,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    cantidad_registros INTEGER NOT NULL,
    media NUMERIC(12,4),
    mediana NUMERIC(12,4),
    desviacion_estandar NUMERIC(12,4),
    minimo NUMERIC(12,4),
    maximo NUMERIC(12,4),
    percentil_25 NUMERIC(12,4),
    percentil_75 NUMERIC(12,4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. Optimización con SciPy
CREATE TABLE optimizaciones (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    parametros_entrada JSONB NOT NULL,
    resultado JSONB,
    costo_inicial NUMERIC(14,4),
    costo_optimizado NUMERIC(14,4),
    estado VARCHAR(30) DEFAULT 'pendiente',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 12. Auditoría
CREATE TABLE auditoria (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT REFERENCES usuarios(id) ON DELETE SET NULL,
    accion VARCHAR(100) NOT NULL,
    tabla VARCHAR(100),
    registro_id BIGINT,
    detalles JSONB,
    ip VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW()
);