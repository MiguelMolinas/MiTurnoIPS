# WORKFLOW.md — Guía de Prompts y Desarrollo Modular

## Regla de Oro
Desarrollar y probar componente por componente. No avanzar al siguiente hasta que el anterior esté validado.

## Fases de Prompting para el IDE

### Fase 1: Bot Base
*Instrucción al Agent*: Generar `main.py`, `bot.py`, `.env.example`, `requirements.txt` y `.gitignore` para poner a correr un bot de Telegram mínimo que responda a `/start` y haga eco de mensajes.

### Fase 2: Extracción con OpenAI
*Instrucción al Agent*: Crear `openai_service.py` utilizando la API oficial de OpenAI en modo JSON para extraer `especialidad` y `clinica`. Conectarlo con el handler de texto en `bot.py`.

### Fase 3: IPS Mock Asíncrono
*Instrucción al Agent*: Crear `ips_mock.py` que simule la búsqueda de turnos médica y devuelva un turno disponible tras un tiempo predecible de reintentos.

### Fase 4: Tarea en Segundo Plano (Asyncio)
*Instrucción al Agent*: Modificar `bot.py` para lanzar una tarea en segundo plano (`asyncio.create_task`) cuando no haya disponibilidad inicial y notificar al usuario cuando el mock devuelva resultado positivo.

### Fase 5: Robustez y Modo Demo
*Instrucción al Agent*: Agregar el comando `/demo` para saltar OpenAI si es necesario y el comando `/cancelar` para detener tareas background asociadas al chat.