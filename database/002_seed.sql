-- database/002_seed.sql
-- Datos iniciales (Seeders) para Empresa Inteligente

-- Insertar Categorías predeterminadas
INSERT INTO categorias (nombre, descripcion) VALUES
('VENTAS', 'Comentarios relacionados con procesos de compra y negociación'),
('SOPORTE', 'Incidencias técnicas y resolución de problemas de plataforma'),
('RECLAMO', 'Quejas formales o inconformidades con el servicio'),
('CONSULTA', 'Preguntas frecuentes y dudas sobre el funcionamiento'),
('FELICITACION', 'Comentarios positivos acerca de la atención o el sistema'),
('OTROS', 'Comentarios generales no categorizados');

-- Insertar Usuario Administrador inicial (password temporal hasheado o mock)
INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES
('Administrador General', 'admin@empresainteligente.com', '$2b$12$e8...mockhash...', 'ADMIN');

-- Insertar Clientes de prueba
INSERT INTO clientes (nombre, email, telefono, empresa) VALUES
('Ana García', 'ana.garcia@techcorp.com', '+51999888777', 'TechCorp S.A.'),
('Carlos Mendoza', 'cmendoza@innovacion.pe', '+51988777666', 'Innovación Andina'),
('Lucía Torres', 'lucia@logistica.com', '+51977666555', 'Logística Global'),
('Jorge Ramírez', 'jorge.ramirez@retailmax.com', '+51966555444', 'RetailMax'),
('Sofía Valdivia', 'svaldivia@finanzas.net', '+51955444333', 'Finanzas Digitales');

-- Insertar Comentarios de ejemplo
INSERT INTO comentarios (cliente_id, contenido, canal, estado, categoria, procesado) VALUES
(1, 'La nueva actualización del módulo de analítica mejoró notablemente el tiempo de respuesta.', 'web', 'procesado', 'FELICITACION', TRUE),
(2, 'El soporte técnico tardó más de lo esperado en resolver nuestra incidencia de facturación.', 'soporte', 'procesado', 'SOPORTE', TRUE),
(3, 'El reporte general cumple con lo básico, pero faltan opciones de exportación avanzada.', 'web', 'pendiente', 'CONSULTA', FALSE),
(4, 'Excelente atención por parte del equipo de ventas durante la negociación del contrato.', 'email', 'procesado', 'VENTAS', TRUE),
(5, 'Tuvimos problemas intermitentes al procesar los datos con los scripts de SciPy.', 'soporte', 'pendiente', 'RECLAMO', FALSE);

-- Insertar Tiempos de atención (para cálculos SciPy)
INSERT INTO tiempos_atencion (cliente_id, comentario_id, tiempo_minutos, operador) VALUES
(1, 1, 12.00, 'María López'),
(2, 2, 15.50, 'Juan Pérez'),
(3, 3, 18.00, 'María López'),
(4, 4, 20.25, 'Carlos Ruiz'),
(5, 5, 11.00, 'Juan Pérez');