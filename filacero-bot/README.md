# FilaCero

FilaCero es un bot de Telegram que interpreta una solicitud médica, consulta disponibilidad de turnos y continúa buscando en segundo plano cuando no encuentra uno de inmediato.

## Arquitectura

- `main.py`: punto de entrada.
- `bot.py`: comandos `/start`, `/demo`, `/cancelar`, `/requisitos` y mensajes de texto.
- `openai_service.py`: extracción estructurada de especialidad y clínica.
- `exa_service.py`: búsqueda opcional de requisitos web con Exa.
- `ips_mock.py`: simulador determinista de liberación de turnos.
- `schema.sql`: esquema y datos mínimos para la demo con MySQL/MariaDB.

## Ejecución

1. Crear un entorno e instalar dependencias:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Completar las variables de `.env`.
3. Crear la base de datos y cargar los datos de demo:

   ```bash
   mysql -u root -p < schema.sql
   ```

4. Ejecutar:

   ```bash
   python main.py
   ```

Para probar el flujo sin consumir OpenAI, usar `/demo` en Telegram. `/cancelar` detiene la búsqueda activa del chat.

`/requisitos pediatría IPS Ingavi` consulta Exa y devuelve enlaces y fragmentos destacados sobre los requisitos de atención. La integración usa el endpoint de búsqueda nativo de Exa con `highlights` para mantener la respuesta breve y útil para una demo.

Las variables `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` y `DB_NAME` configuran la conexión de `ips_mock.py`. El archivo `.env` es local y no debe subirse al repositorio.
