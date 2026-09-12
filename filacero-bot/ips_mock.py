"""Simulador determinista de disponibilidad de turnos."""

import asyncio
from collections import defaultdict

_ATTEMPTS: defaultdict[tuple[str, str], int] = defaultdict(int)


async def check_availability(especialidad: str, clinica: str) -> dict[str, str] | None:
    """Devuelve un turno después de algunos reintentos simulados."""
    await asyncio.sleep(0.1)
    key = (especialidad.lower(), clinica.lower())
    _ATTEMPTS[key] += 1
    if _ATTEMPTS[key] < 3:
        return None
    return {
        "especialidad": especialidad,
        "clinica": clinica,
        "fecha": "mañana",
        "hora": "09:30",
    }
