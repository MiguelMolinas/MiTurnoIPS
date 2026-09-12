# Mi_Turno_IPS


> **“Sin Telegram, el paciente tendría que quedarse esperando frente a una pantalla de IPS recargando la página. Gracias a estar en un canal de mensajería, el agente lo interrumpe solo cuando hay novedades y el usuario puede seguir con su día.”**

<<<<<<< HEAD
- `main.py`: punto de entrada.
- `bot.py`: comandos `/start`, `/demo`, `/cancelar`, `/requisitos` y mensajes de texto.
- `openai_service.py`: extracción estructurada de especialidad y clínica.
- `exa_service.py`: búsqueda opcional de requisitos web con Exa.
- `ips_mock.py`: simulador determinista de liberación de turnos.
- `schema.sql`: esquema y datos mínimos para la demo con MySQL/MariaDB.
=======
Mi Turno IPS es un agente inteligente diseñado para resolver un problema masivo y cotidiano en el sistema de salud: la fricción de conseguir un turno médico.
>>>>>>> 03b8a44 (Feature All)

## El Problema
Conseguir una cita médica exige tiempo, llamadas interminables, reintentos o estar refrescando un sistema web colapsado a la espera de un espacio. La disponibilidad es dinámica: un turno que no existe a las 8:00 AM puede aparecer a las 10:00 AM por una cancelación, pero el usuario no tiene tiempo para estar vigilando.

## La Solución
El usuario simplemente le escribe a nuestro agente a través de **Telegram** en lenguaje natural (ej. *"Necesito pediatría en IPS Ingavi"*). 

El agente:
1. Interpreta la intención y extrae los datos clave (especialidad, establecimiento).
2. Consulta la disponibilidad.
3. **Si no hay turnos**, no descarta al usuario: deja una tarea trabajando en segundo plano.
4. **Notifica proactivamente** cuando se libera un espacio.

<<<<<<< HEAD
2. Completar las variables de `.env`.
3. Crear la base de datos y cargar los datos de demo:

   ```bash
   mysql -u root -p < schema.sql
   ```

4. Ejecutar:
=======
## El momento "Wow"
El usuario deja de hacer el trabajo pesado. **No necesita seguir refrescando una página ni volver a preguntar.** El agente asume la carga mental, continúa trabajando de forma invisible y vuelve al usuario únicamente cuando tiene un resultado exitoso.
>>>>>>> 03b8a44 (Feature All)

---

<<<<<<< HEAD
Para probar el flujo sin consumir OpenAI, usar `/demo` en Telegram. `/cancelar` detiene la búsqueda activa del chat.

`/requisitos pediatría IPS Ingavi` consulta Exa y devuelve enlaces y fragmentos destacados sobre los requisitos de atención. La integración usa el endpoint de búsqueda nativo de Exa con `highlights` para mantener la respuesta breve y útil para una demo.

Las variables `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` y `DB_NAME` configuran la conexión de `ips_mock.py`. El archivo `.env` es local y no debe subirse al repositorio.
=======
## Flujo y Arquitectura

El sistema está construido en Python y utiliza un enfoque asíncrono para mantener la búsqueda de turnos en segundo plano sin bloquear el sistema. Los componentes clave son:

* **`main.py` & `bot.py` (Interfaz en Telegram):** Inicializan el bot y manejan la interacción con el usuario mediante comandos y lenguaje natural.
* **`openai_service.py` (Cerebro IA - Integración Real):** **(Prioridad Estratégica)** No hay respuestas pregrabadas. El agente se conecta en tiempo real a la API de OpenAI. La función `parse_user_request()` procesa el texto del usuario para entender su intención y extraer entidades estructuradas (ej. `{"especialidad": "Pediatría", "clinica": "IPS Ingavi"}`).
* **`ips_mock.py` (Simulador de Disponibilidad):** La función `check_availability()` verifica si hay lugares. Si el turno existe, se devuelve inmediatamente.
* **Vigilancia Asíncrona:** Si no hay lugares, el sistema no descarta al usuario. Genera un `asyncio.create_task()` que consulta periódicamente a `ips_mock.py` de forma silenciosa. Al liberarse un espacio en el simulador, esta tarea de fondo lanza la notificación proactiva al chat de Telegram del usuario.

---

## ⚠️ Aclaración sobre el Prototipo (Mock)

Este proyecto es una **demostración técnica** diseñada para validar la experiencia de usuario y la arquitectura de un agente autónomo frente a la problemática real de agendamiento médico en Paraguay.

**⚠️ Nota: El sistema utiliza un mock (ips_mock.py) para simular la disponibilidad de IPS. No está conectado a sistemas gubernamentales reales.**

La integración con los modelos de lenguaje de OpenAI para interpretar los pedidos es **100% real y funcional en la demostración**, pero la disponibilidad de los turnos está aislada y controlada mediante un entorno simulado para poder evaluar la respuesta del agente ante cambios dinámicos de agenda.

---

## Instalación y Ejecución Local

Para levantar el proyecto en tu entorno local (ej. durante el Hackathon), sigue estos pasos.

### 1. Clonar el repositorio y preparar el entorno
```bash
git clone <URL_DEL_REPOSITORIO>
cd filacero-bot
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate
# Activar entorno (Mac/Linux)
source venv/bin/activate
>>>>>>> 03b8a44 (Feature All)
