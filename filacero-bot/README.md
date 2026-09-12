# FilaCero

FilaCero es un bot de Telegram que interpreta una solicitud médica, consulta disponibilidad de turnos y continúa buscando en segundo plano cuando no encuentra uno de inmediato.

## Arquitectura

- `main.py`: punto de entrada.
- `bot.py`: comandos `/start`, `/demo`, `/cancelar` y mensajes de texto.
- `openai_service.py`: extracción estructurada de especialidad y clínica.
- `exa_service.py`: búsqueda opcional de requisitos web con Exa.
- `ips_mock.py`: simulador determinista de liberación de turnos.

## Ejecución

1. Crear un entorno e instalar dependencias:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Completar las variables de `.env`.
3. Ejecutar:

   ```bash
   python main.py
   ```

Para probar el flujo sin consumir OpenAI, usar `/demo` en Telegram. `/cancelar` detiene la búsqueda activa del chat.
