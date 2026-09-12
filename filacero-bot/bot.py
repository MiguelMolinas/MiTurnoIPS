"""Handlers de Telegram y coordinación de búsquedas de turnos."""

import asyncio
import logging
import os
from typing import Any

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from exa_service import find_requirements
from ips_mock import buscar_turno, cancelar_solicitud, crear_solicitud
from openai_service import parse_user_request

load_dotenv()
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

BACKGROUND_TASKS: dict[int, asyncio.Task[None]] = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Presenta el bot al usuario."""
    if update.message:
        await update.message.reply_text(
            "Hola, soy FilaCero. Escribime qué especialidad y clínica necesitás."
        )


async def demo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ejecuta una búsqueda determinista sin llamar a OpenAI."""
    await _handle_request(update, "pediatria en IPS Ingavi", use_ai=False)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancela la búsqueda activa del chat."""
    if not update.effective_chat or not update.message:
        return
    chat_id = update.effective_chat.id
    task = BACKGROUND_TASKS.pop(chat_id, None)
    if task:
        task.cancel()
    result = await asyncio.to_thread(cancelar_solicitud, chat_id)
    if not result.get("ok"):
        await update.message.reply_text("No pude cancelar la búsqueda.")
    elif result.get("cancelado"):
        await update.message.reply_text("Búsqueda cancelada.")
    else:
        await update.message.reply_text("No hay una búsqueda activa.")


async def requirements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Busca en la web los requisitos de una atención médica."""
    if not update.message:
        return
    query = " ".join(context.args).strip()
    if not query:
        await update.message.reply_text(
            "Usá /requisitos seguido de la especialidad y la clínica."
        )
        return

    try:
        results = await asyncio.to_thread(find_requirements, query)
        if not results:
            await update.message.reply_text(
                "No encontré requisitos. Verificá EXA_API_KEY o probá otra consulta."
            )
            return
        await update.message.reply_text(_format_requirements(query, results))
    except Exception:
        LOGGER.exception("Error buscando requisitos con Exa")
        await update.message.reply_text("No pude consultar los requisitos ahora.")


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Interpreta una solicitud normal del usuario."""
    if update.message:
        await _handle_request(update, update.message.text or "", use_ai=True)


async def _handle_request(update: Update, text: str, use_ai: bool) -> None:
    if not update.effective_chat or not update.message:
        return

    try:
        request = (
            await asyncio.to_thread(parse_user_request, text)
            if use_ai
            else {"especialidad": "Pediatría", "clinica": "IPS Ingavi"}
        )
        specialty = request.get("especialidad")
        clinic = request.get("clinica")
        if not specialty or not clinic:
            await update.message.reply_text(
                "Necesito una especialidad y una clínica para buscar el turno."
            )
            return

        user_name = update.effective_user.full_name if update.effective_user else None
        request = await asyncio.to_thread(
            crear_solicitud,
            update.effective_chat.id,
            specialty,
            clinic,
            user_name,
        )
        if not request.get("ok"):
            await update.message.reply_text(request.get("error", "No pude crear la búsqueda."))
            return

        request_id = request["solicitud_id"]
        availability = await asyncio.to_thread(buscar_turno, request_id)
        if availability.get("disponible"):
            await update.message.reply_text(_format_appointment(availability))
            return
        if not availability.get("ok"):
            await update.message.reply_text(availability.get("error", "No pude buscar turnos."))
            return

        await update.message.reply_text(
            f"No hay turnos ahora. Voy a buscar {specialty} en {clinic} en segundo plano."
        )
        chat_id = update.effective_chat.id
        old_task = BACKGROUND_TASKS.pop(chat_id, None)
        if old_task:
            old_task.cancel()
        BACKGROUND_TASKS[chat_id] = asyncio.create_task(
            _watch_availability(chat_id, request_id, update.get_bot())
        )
    except Exception:
        LOGGER.exception("Error procesando la solicitud")
        await update.message.reply_text("No pude procesar la solicitud. Probá de nuevo.")


async def _watch_availability(chat_id: int, request_id: int, bot: Any) -> None:
    try:
        while True:
            await asyncio.sleep(5)
            availability = await asyncio.to_thread(buscar_turno, request_id)
            if availability.get("disponible"):
                await bot.send_message(chat_id, _format_appointment(availability))
                return
            if not availability.get("ok") or availability.get("cancelado"):
                return
    except asyncio.CancelledError:
        raise
    except Exception:
        LOGGER.exception("Error en la búsqueda de fondo para %s", chat_id)
    finally:
        BACKGROUND_TASKS.pop(chat_id, None)


def _format_appointment(appointment: dict[str, str]) -> str:
    return (
        "¡Encontré un turno!\n"
        f"Especialidad: {appointment['especialidad']}\n"
        f"Clínica: {appointment['clinica']}\n"
        f"Fecha: {appointment['fecha']} a las {appointment['hora']}"
    )


def _format_requirements(query: str, results: list[dict[str, Any]]) -> str:
    lines = [f"Requisitos encontrados para: {query}"]
    for result in results:
        lines.append(f"\n{result['title']}\n{result['url']}")
        highlights = result.get("highlights", [])
        if highlights:
            lines.append(str(highlights[0]))
    return "\n".join(lines)


def build_application() -> Application:
    """Construye la aplicación de Telegram."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN en el archivo .env")
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("demo", demo))
    application.add_handler(CommandHandler("cancelar", cancel))
    application.add_handler(CommandHandler("requisitos", requirements))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    return application
