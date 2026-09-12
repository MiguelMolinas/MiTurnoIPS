CREATE DATABASE IF NOT EXISTS mtips;
USE mtips;

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    telegram_chat_id BIGINT NOT NULL UNIQUE,
    nombre VARCHAR(255),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clinica (
    id_clinica INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS especialidad (
    id_especialidad INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS turno (
    id_turno INT AUTO_INCREMENT PRIMARY KEY,
    id_clinica INT NOT NULL,
    id_especialidad INT NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    estado ENUM('DISPONIBLE', 'RESERVADO') NOT NULL DEFAULT 'DISPONIBLE',
    visible BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (id_clinica) REFERENCES clinica(id_clinica),
    FOREIGN KEY (id_especialidad) REFERENCES especialidad(id_especialidad),
    INDEX idx_turno_busqueda (id_clinica, id_especialidad, estado, visible)
);

CREATE TABLE IF NOT EXISTS solicitud (
    id_solicitud INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_clinica INT NOT NULL,
    id_especialidad INT NOT NULL,
    id_turno INT NULL,
    estado ENUM('BUSCANDO', 'ENCONTRADO', 'CANCELADO') NOT NULL DEFAULT 'BUSCANDO',
    intentos INT NOT NULL DEFAULT 0,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario),
    FOREIGN KEY (id_clinica) REFERENCES clinica(id_clinica),
    FOREIGN KEY (id_especialidad) REFERENCES especialidad(id_especialidad),
    FOREIGN KEY (id_turno) REFERENCES turno(id_turno),
    INDEX idx_solicitud_usuario_estado (id_usuario, estado, fecha_creacion)
);

INSERT INTO clinica (nombre)
VALUES ('IPS Ingavi')
ON DUPLICATE KEY UPDATE nombre = VALUES(nombre);

INSERT INTO especialidad (nombre)
VALUES ('Pediatría')
ON DUPLICATE KEY UPDATE nombre = VALUES(nombre);

INSERT INTO turno (id_clinica, id_especialidad, fecha, hora, estado, visible)
SELECT c.id_clinica, e.id_especialidad, CURRENT_DATE + INTERVAL 1 DAY, '09:30:00', 'DISPONIBLE', FALSE
FROM clinica c
JOIN especialidad e
WHERE c.nombre = 'IPS Ingavi'
  AND e.nombre = 'Pediatría'
  AND NOT EXISTS (
      SELECT 1
      FROM turno t
      WHERE t.id_clinica = c.id_clinica
        AND t.id_especialidad = e.id_especialidad
        AND t.fecha = CURRENT_DATE + INTERVAL 1 DAY
        AND t.hora = '09:30:00'
  );
