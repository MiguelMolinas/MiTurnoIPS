# ARCHITECTURE.md — Flujo y Componentes de FilaCero

## Flujo Conversacional y de Datos
1. **Entrada de Usuario**: El usuario envía un mensaje en lenguaje natural por Telegram (ej: "Necesito pediatría en IPS Ingavi")[cite: 1].
2. **Comprensión (OpenAI)**: `openai_service.py` procesa el texto y extrae `{"especialidad": "Pediatría", "clinica": "IPS Ingavi"}`[cite: 1].
3. **Consulta de Disponibilidad**: `ips_mock.py` verifica disponibilidad[cite: 1].
   - **Caso A (Disponible)**: Devuelve el turno e informa al usuario de inmediato[cite: 1].
   - **Caso B (No disponible)**: Notifica al usuario que activó la búsqueda asíncrona y genera un `asyncio.create_task()`[cite: 1].
4. **Vigilancia en Segundo Plano**: El bucle asíncrono consulta periódicamente `ips_mock.py`[cite: 1].
5. **Notificación Proactiva**: Al liberarse un turno en el mock, la tarea de fondo envía un mensaje formateado al `chat_id` original[cite: 1].

## Definición de Componentes Clave
- `main.py`: Inicializa el bot y el event loop[cite: 1].
- `bot.py`: Registra los handlers de Telegram (`/start`, `/demo`, `/cancelar` y mensajes de texto)[cite: 1].
- `openai_service.py`: Función `parse_user_request(user_text: str)` -> dict[cite: 1].
- `ips_mock.py`: Función `check_availability(especialidad, clinica)` -> dict[cite: 1].