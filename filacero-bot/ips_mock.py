"""
<<<<<<< HEAD
ips_mock.py
Mock autocontenido

Requisitos:
    pip install mysql-connector-python

Este archivo:
- se conecta directamente a MySQL/MariaDB,
- no depende de Flask ni de SQLAlchemy,
- crea solicitudes,
- busca turnos,
- simula disponibilidad tras N intentos,
- cancela solicitudes,
- permite liberar turnos manualmente.

La base de datos esperada contiene estas tablas:
- usuario
- clinica
- especialidad
- turno
- solicitud

IMPORTANTE:
Configura los datos de conexión en DB_CONFIG.
"""

import os
from typing import Any

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURACIÓN
# ============================================================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "mtips"),
    "port": int(os.getenv("DB_PORT", "3306")),
}

# Cantidad de consultas antes de que el mock haga visible
# automáticamente un turno oculto.
INTENTOS_PARA_LIBERAR = 3


# ============================================================
# CONEXIÓN
# ============================================================

def obtener_conexion():
    """
    Abre una conexión nueva a MySQL.

    Retorna:
        objeto conexión

    Lanza:
        mysql.connector.Error si la conexión falla.
    """
    return mysql.connector.connect(**DB_CONFIG)


# ============================================================
# UTILIDADES
# ============================================================

def _cerrar(cursor: Any = None, conexion: Any = None):
    """Cierra cursor y conexión de forma segura."""
    if cursor is not None:
        try:
            cursor.close()
        except Exception:
            pass

    if conexion is not None:
        try:
            if conexion.is_connected():
                conexion.close()
        except Exception:
            pass


def _obtener_usuario_por_chat(cursor: Any, chat_id: int) -> dict[str, Any] | None:
    cursor.execute(
        """
        SELECT id_usuario, telegram_chat_id
        FROM usuario
        WHERE telegram_chat_id = %s
        """,
        (chat_id,)
    )
    return cursor.fetchone()


def _obtener_clinica_por_nombre(cursor: Any, nombre: str) -> dict[str, Any] | None:
    cursor.execute(
        """
        SELECT id_clinica, nombre
        FROM clinica
        WHERE nombre = %s
        """,
        (nombre,)
    )
    return cursor.fetchone()


def _obtener_especialidad_por_nombre(cursor: Any, nombre: str) -> dict[str, Any] | None:
    cursor.execute(
        """
        SELECT id_especialidad, nombre
        FROM especialidad
        WHERE nombre = %s
        """,
        (nombre,)
    )
    return cursor.fetchone()


# ============================================================
# SOLICITUDES
# ============================================================

def crear_solicitud(chat_id, especialidad_nombre, clinica_nombre, nombre_usuario=None):
    """
    Crea una nueva solicitud de búsqueda.

    Si el usuario no existe, lo crea automáticamente.

    Ejemplo:
        crear_solicitud(
            123456789,
            "Pediatría",
            "IPS Ingavi",
            "Juan"
        )

    Retorna:
        {
            "ok": True,
            "solicitud_id": 1
        }

    o:
        {
            "ok": False,
            "error": "..."
        }
    """

    conexion = None
    cursor: Any = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        # --------------------------------------------
        # Buscar o crear usuario
        # --------------------------------------------
        usuario = _obtener_usuario_por_chat(cursor, chat_id)

        if usuario is None:
            cursor.execute(
                """
                INSERT INTO usuario (
                    telegram_chat_id,
                    nombre
                )
                VALUES (%s, %s)
                """,
                (chat_id, nombre_usuario)
            )

            id_usuario = cursor.lastrowid

        else:
            id_usuario = usuario["id_usuario"]

        # --------------------------------------------
        # Buscar clínica
        # --------------------------------------------
        clinica = _obtener_clinica_por_nombre(
            cursor,
            clinica_nombre
        )

        if clinica is None:
            conexion.rollback()

            return {
                "ok": False,
                "error": f"Clínica no encontrada: {clinica_nombre}"
            }

        # --------------------------------------------
        # Buscar especialidad
        # --------------------------------------------
        especialidad = _obtener_especialidad_por_nombre(
            cursor,
            especialidad_nombre
        )

        if especialidad is None:
            conexion.rollback()

            return {
                "ok": False,
                "error": f"Especialidad no encontrada: {especialidad_nombre}"
            }

        # --------------------------------------------
        # Crear solicitud
        # --------------------------------------------
        cursor.execute(
            """
            INSERT INTO solicitud (
                id_usuario,
                id_clinica,
                id_especialidad,
                estado,
                intentos
            )
            VALUES (%s, %s, %s, 'BUSCANDO', 0)
            """,
            (
                id_usuario,
                clinica["id_clinica"],
                especialidad["id_especialidad"]
            )
        )

        id_solicitud = cursor.lastrowid

        conexion.commit()

        return {
            "ok": True,
            "solicitud_id": id_solicitud
        }

    except Error as e:
        if conexion is not None:
            conexion.rollback()

        return {
            "ok": False,
            "error": f"Error de base de datos: {e}"
        }

    finally:
        _cerrar(cursor, conexion)


# ============================================================
# BÚSQUEDA DE TURNOS
# ============================================================

def buscar_turno(solicitud_id):
    """
    Simula una consulta al sistema IPS.

    Funcionamiento:
    1. Obtiene la solicitud.
    2. Si está CANCELADA, termina.
    3. Si ya está ENCONTRADA, devuelve el mismo turno.
    4. Incrementa intentos.
    5. Al alcanzar INTENTOS_PARA_LIBERAR,
       hace visible un turno oculto compatible.
    6. Busca el primer turno visible y DISPONIBLE.
    7. Si lo encuentra:
       - asigna el turno,
       - marca solicitud ENCONTRADO,
       - marca turno RESERVADO.

    Retorna:
        diccionario estructurado.
    """

    conexion = None
    cursor: Any = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        # --------------------------------------------
        # Obtener solicitud
        # --------------------------------------------
        cursor.execute(
            """
            SELECT
                id_solicitud,
                id_usuario,
                id_clinica,
                id_especialidad,
                id_turno,
                estado,
                intentos
            FROM solicitud
            WHERE id_solicitud = %s
            """,
            (solicitud_id,)
        )

        solicitud = cursor.fetchone()

        if solicitud is None:
            return {
                "ok": False,
                "error": "Solicitud inexistente"
            }

        # --------------------------------------------
        # Solicitud cancelada
        # --------------------------------------------
        if solicitud["estado"] == "CANCELADO":
            return {
                "ok": True,
                "cancelado": True,
                "disponible": False
            }

        # --------------------------------------------
        # Ya encontró un turno
        # --------------------------------------------
        if solicitud["estado"] == "ENCONTRADO":
            return _obtener_respuesta_turno(
                cursor,
                solicitud["id_turno"],
                solicitud["intentos"]
            )

        # --------------------------------------------
        # Incrementar intentos
        # --------------------------------------------
        nuevos_intentos = solicitud["intentos"] + 1

        cursor.execute(
            """
            UPDATE solicitud
            SET intentos = %s
            WHERE id_solicitud = %s
            """,
            (
                nuevos_intentos,
                solicitud_id
            )
        )

        # --------------------------------------------
        # Simular aparición de disponibilidad
        # --------------------------------------------
        if nuevos_intentos >= INTENTOS_PARA_LIBERAR:

            cursor.execute(
                """
                SELECT id_turno
                FROM turno
                WHERE id_clinica = %s
                  AND id_especialidad = %s
                  AND estado = 'DISPONIBLE'
                  AND visible = FALSE
                ORDER BY fecha ASC, hora ASC
                LIMIT 1
                """,
                (
                    solicitud["id_clinica"],
                    solicitud["id_especialidad"]
                )
            )

            turno_oculto = cursor.fetchone()

            if turno_oculto is not None:
                cursor.execute(
                    """
                    UPDATE turno
                    SET visible = TRUE
                    WHERE id_turno = %s
                    """,
                    (turno_oculto["id_turno"],)
                )

        # --------------------------------------------
        # Buscar turno disponible visible
        # --------------------------------------------
        cursor.execute(
            """
            SELECT
                t.id_turno,
                t.fecha,
                t.hora,
                c.nombre AS clinica,
                e.nombre AS especialidad
            FROM turno t
            INNER JOIN clinica c
                ON t.id_clinica = c.id_clinica
            INNER JOIN especialidad e
                ON t.id_especialidad = e.id_especialidad
            WHERE t.id_clinica = %s
              AND t.id_especialidad = %s
              AND t.estado = 'DISPONIBLE'
              AND t.visible = TRUE
            ORDER BY t.fecha ASC, t.hora ASC
            LIMIT 1
            """,
            (
                solicitud["id_clinica"],
                solicitud["id_especialidad"]
            )
        )

        turno = cursor.fetchone()

        # --------------------------------------------
        # Sin disponibilidad
        # --------------------------------------------
        if turno is None:
            conexion.commit()

            return {
                "ok": True,
                "disponible": False,
                "cancelado": False,
                "intentos": nuevos_intentos
            }

        # --------------------------------------------
        # Asignar turno
        # --------------------------------------------
        cursor.execute(
            """
            UPDATE solicitud
            SET
                id_turno = %s,
                estado = 'ENCONTRADO'
            WHERE id_solicitud = %s
            """,
            (
                turno["id_turno"],
                solicitud_id
            )
        )

        # Reservar el turno para evitar que otro usuario
        # reciba exactamente el mismo.
        cursor.execute(
            """
            UPDATE turno
            SET estado = 'RESERVADO'
            WHERE id_turno = %s
            """,
            (turno["id_turno"],)
        )

        conexion.commit()

        return {
            "ok": True,
            "disponible": True,
            "cancelado": False,
            "intentos": nuevos_intentos,
            "turno_id": turno["id_turno"],
            "clinica": turno["clinica"],
            "especialidad": turno["especialidad"],
            "fecha": turno["fecha"].isoformat(),
            "hora": str(turno["hora"])[:5]
        }

    except Error as e:
        if conexion is not None:
            conexion.rollback()

        return {
            "ok": False,
            "error": f"Error de base de datos: {e}"
        }

    finally:
        _cerrar(cursor, conexion)


def _obtener_respuesta_turno(cursor: Any, turno_id: int, intentos: int) -> dict[str, Any]:
    """
    Obtiene la información de un turno ya asignado.
    """

    if turno_id is None:
        return {
            "ok": False,
            "error": "La solicitud no tiene un turno asociado"
        }

    cursor.execute(
        """
        SELECT
            t.id_turno,
            t.fecha,
            t.hora,
            c.nombre AS clinica,
            e.nombre AS especialidad
        FROM turno t
        INNER JOIN clinica c
            ON t.id_clinica = c.id_clinica
        INNER JOIN especialidad e
            ON t.id_especialidad = e.id_especialidad
        WHERE t.id_turno = %s
        """,
        (turno_id,)
    )

    turno = cursor.fetchone()

    if turno is None:
        return {
            "ok": False,
            "error": "Turno asociado inexistente"
        }

    return {
        "ok": True,
        "disponible": True,
        "cancelado": False,
        "intentos": intentos,
        "turno_id": turno["id_turno"],
        "clinica": turno["clinica"],
        "especialidad": turno["especialidad"],
        "fecha": turno["fecha"].isoformat(),
        "hora": str(turno["hora"])[:5]
    }


# ============================================================
# CANCELACIÓN
# ============================================================

def cancelar_solicitud(chat_id):
    """
    Cancela la búsqueda BUSCANDO más reciente
    asociada al usuario de Telegram.

    Retorna:
        {
            "ok": True,
            "cancelado": True
        }

    o:
        {
            "ok": True,
            "cancelado": False
        }
    """

    conexion = None
    cursor: Any = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        usuario = _obtener_usuario_por_chat(
            cursor,
            chat_id
        )

        if usuario is None:
            return {
                "ok": True,
                "cancelado": False
            }

        cursor.execute(
            """
            SELECT id_solicitud
            FROM solicitud
            WHERE id_usuario = %s
              AND estado = 'BUSCANDO'
            ORDER BY fecha_creacion DESC
            LIMIT 1
            """,
            (usuario["id_usuario"],)
        )

        solicitud = cursor.fetchone()

        if solicitud is None:
            return {
                "ok": True,
                "cancelado": False
            }

        cursor.execute(
            """
            UPDATE solicitud
            SET estado = 'CANCELADO'
            WHERE id_solicitud = %s
            """,
            (solicitud["id_solicitud"],)
        )

        conexion.commit()

        return {
            "ok": True,
            "cancelado": True,
            "solicitud_id": solicitud["id_solicitud"]
        }

    except Error as e:
        if conexion is not None:
            conexion.rollback()

        return {
            "ok": False,
            "error": f"Error de base de datos: {e}"
        }

    finally:
        _cerrar(cursor, conexion)


# ============================================================
# LIBERACIÓN MANUAL DE TURNOS
# ============================================================

def liberar_turno(turno_id):
    """
    Hace visible manualmente un turno DISPONIBLE.

    Útil durante una demo para simular que acaba
    de aparecer una cancelación en IPS.
    """

    conexion = None
    cursor: Any = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id_turno, estado
            FROM turno
            WHERE id_turno = %s
            """,
            (turno_id,)
        )

        turno = cursor.fetchone()

        if turno is None:
            return {
                "ok": False,
                "error": "Turno inexistente"
            }

        if turno["estado"] != "DISPONIBLE":
            return {
                "ok": False,
                "error": "El turno no está disponible"
            }

        cursor.execute(
            """
            UPDATE turno
            SET visible = TRUE
            WHERE id_turno = %s
            """,
            (turno_id,)
        )

        conexion.commit()

        return {
            "ok": True,
            "turno_id": turno_id,
            "visible": True
        }

    except Error as e:
        if conexion is not None:
            conexion.rollback()

        return {
            "ok": False,
            "error": f"Error de base de datos: {e}"
        }

    finally:
        _cerrar(cursor, conexion)


# ============================================================
# ESTADO DE UNA SOLICITUD
# ============================================================

def obtener_estado_solicitud(solicitud_id):
    """
    Devuelve el estado actual de una solicitud.
    """

    conexion = None
    cursor: Any = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id_solicitud,
                estado,
                intentos,
                id_turno,
                fecha_creacion,
                fecha_actualizacion
            FROM solicitud
            WHERE id_solicitud = %s
            """,
            (solicitud_id,)
        )

        solicitud = cursor.fetchone()

        if solicitud is None:
            return {
                "ok": False,
                "error": "Solicitud inexistente"
            }

        return {
            "ok": True,
            "solicitud_id": solicitud["id_solicitud"],
            "estado": solicitud["estado"],
            "intentos": solicitud["intentos"],
            "turno_id": solicitud["id_turno"],
            "fecha_creacion": str(solicitud["fecha_creacion"]),
            "fecha_actualizacion": str(solicitud["fecha_actualizacion"])
        }

    except Error as e:
        return {
            "ok": False,
            "error": f"Error de base de datos: {e}"
        }

    finally:
        _cerrar(cursor, conexion)


# ============================================================
# PRUEBA LOCAL
# ============================================================

if __name__ == "__main__":

    print("=== PRUEBA DEL IPS MOCK ===")

    chat_id_prueba = 999999999

    resultado = crear_solicitud(
        chat_id=chat_id_prueba,
        especialidad_nombre="Pediatría",
        clinica_nombre="IPS Ingavi",
        nombre_usuario="Usuario Demo"
    )

    print("Crear solicitud:")
    print(resultado)

    if resultado.get("ok"):

        solicitud_id = resultado["solicitud_id"]

        print("\nBuscando turnos...")

        for numero in range(1, 5):

            respuesta = buscar_turno(
                solicitud_id
            )

            print(
                f"Intento {numero}:",
                respuesta
            )

            if respuesta.get("disponible"):
                break
=======
ips_mock.py (Versión Hackathon en Memoria)
No requiere SQL. No requiere instalar nada.
Simula la disponibilidad en memoria RAM para grabar la demo rápido.
"""

# Base de datos falsa en la memoria de Python
solicitudes_db = {}
contador_id = 1

def crear_solicitud(chat_id, especialidad_nombre, clinica_nombre, nombre_usuario=None):
    """Finge guardar la solicitud en una base de datos."""
    global contador_id
    
    solicitudes_db[contador_id] = {
        "chat_id": chat_id,
        "especialidad": especialidad_nombre,
        "clinica": clinica_nombre,
        "estado": "BUSCANDO",
        "intentos": 0
    }
    
    id_actual = contador_id
    contador_id += 1
    
    return {"ok": True, "solicitud_id": id_actual}


def buscar_turno(solicitud_id):
    """
    Finge buscar un turno.
    Al tercer intento (15 segundos de espera), mágicamente 'encuentra' uno.
    """
    if solicitud_id not in solicitudes_db:
        return {"ok": False, "error": "Solicitud inexistente"}
        
    solicitud = solicitudes_db[solicitud_id]
    
    # Si el usuario la canceló
    if solicitud["estado"] == "CANCELADO":
        return {"ok": True, "cancelado": True, "disponible": False}
        
    solicitud["intentos"] += 1
    
    # ¡LA MAGIA DEL MOCK! Al 3er intento fingimos que alguien canceló su turno y se liberó.
    if solicitud["intentos"] >= 3:
        solicitud["estado"] = "ENCONTRADO"
        return {
            "ok": True,
            "disponible": True,
            "cancelado": False,
            "especialidad": solicitud["especialidad"],
            "clinica": solicitud["clinica"],
            "fecha": "Viernes 18/09/2026", # Fecha ficticia para la demo
            "hora": "08:00 AM"
        }
        
    # Si aún no es el 3er intento, seguimos diciendo que no hay turno
    return {
        "ok": True,
        "disponible": False,
        "cancelado": False
    }


def cancelar_solicitud(chat_id):
    """Busca la solicitud del usuario y la cancela."""
    cancelado_exitoso = False
    
    for req_id, req in solicitudes_db.items():
        if req["chat_id"] == chat_id and req["estado"] == "BUSCANDO":
            req["estado"] = "CANCELADO"
            cancelado_exitoso = True
            
    return {"ok": True, "cancelado": cancelado_exitoso}
>>>>>>> 03b8a44 (Feature All)
