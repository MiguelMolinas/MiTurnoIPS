import os
import asyncio
import logging
import html

from dotenv import load_dotenv

from telegram import Update, constants
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from openai_service import (
    analizar_mensaje,
    responder_duda_ips
)

from exa_service import buscar_info_exa

import ips_mock


# ============================================================
# CONFIGURACIÓN
# ============================================================

logging.basicConfig(
    format=(
        "%(asctime)s - "
        "%(name)s - "
        "%(levelname)s - "
        "%(message)s"
    ),
    level=logging.INFO
)

load_dotenv()


# ============================================================
# VIGILANCIA ASÍNCRONA DE TURNOS
# ============================================================

async def vigilar_turnos(
    chat_id: int,
    solicitud_id: int,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Vigila periódicamente si aparece un turno.
    """

    try:

        while True:

            respuesta = ips_mock.buscar_turno(
                solicitud_id
            )

            if not respuesta.get("ok"):
                break

            if respuesta.get("cancelado"):

                logging.info(
                    f"Solicitud {solicitud_id} cancelada."
                )

                break

            if respuesta.get("disponible"):

                especialidad = html.escape(
                    str(
                        respuesta.get(
                            "especialidad",
                            ""
                        )
                    )
                )

                clinica = html.escape(
                    str(
                        respuesta.get(
                            "clinica",
                            ""
                        )
                    )
                )

                fecha = html.escape(
                    str(
                        respuesta.get(
                            "fecha",
                            ""
                        )
                    )
                )

                hora = html.escape(
                    str(
                        respuesta.get(
                            "hora",
                            ""
                        )
                    )
                )

                ticket = (
                    "🔔 <b>¡TURNO CONFIRMADO!</b> 🎉\n\n"
                    "Hemos capturado una cancelación "
                    "para vos:\n\n"

                    f"🩺 <b>Especialidad:</b> "
                    f"{especialidad}\n"

                    f"🏥 <b>Clínica:</b> "
                    f"{clinica}\n"

                    f"📅 <b>Fecha:</b> "
                    f"{fecha}\n"

                    f"⏰ <b>Hora:</b> "
                    f"{hora}\n\n"

                    "<i>¡Mi turno IPS te devuelve "
                    "tu tiempo!</i> 💚"
                )

                await context.bot.send_message(
                    chat_id=chat_id,
                    text=ticket,
                    parse_mode=constants.ParseMode.HTML
                )

                break

            # En la demo esperamos 5 segundos.
            await asyncio.sleep(5)

    except asyncio.CancelledError:

        logging.info(
            f"Vigilancia {solicitud_id} cancelada."
        )

    except Exception as e:

        logging.exception(
            f"Error en vigilancia asíncrona: {e}"
        )


# ============================================================
# /START
# ============================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    mensaje = (
        "👋 ¡Hola! Soy <b>Mi turno IPS</b>.\n\n"

        "No te pediré contraseñas ni te haré navegar "
        "por botones.\n\n"

        "Simplemente decime, con tus propias palabras, "
        "qué especialidad y en qué clínica del IPS "
        "necesitás turno.\n\n"

        "<i>Ejemplo:</i>\n"
        "\"Necesito un pediatra en Ingavi y quiero saber "
        "qué documentos tengo que llevar.\""
    )

    await update.message.reply_text(
        mensaje,
        parse_mode=constants.ParseMode.HTML
    )


# ============================================================
# /CANCELAR
# ============================================================

async def cancelar_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    resultado = ips_mock.cancelar_solicitud(
        chat_id
    )

    if resultado.get("cancelado"):

        await update.message.reply_text(
            "❌ He detenido la vigilancia de tus turnos. "
            "Ya no te notificaré."
        )

    else:

        await update.message.reply_text(
            "No tenés ninguna búsqueda activa "
            "en este momento."
        )


# ============================================================
# PROCESAMIENTO DE MENSAJES
# ============================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message or not update.message.text:
        return

    texto_usuario = update.message.text

    chat_id = update.effective_chat.id

    nombre_usuario = (
        update.effective_user.first_name
        if update.effective_user
        else "Usuario"
    )

    msg_espera = await update.message.reply_text(
        "⏳ Analizando tu solicitud..."
    )

    # --------------------------------------------------------
    # 1. OpenAI interpreta el mensaje
    # --------------------------------------------------------

    datos = await analizar_mensaje(
        texto_usuario
    )

    if "error" in datos:

        await msg_espera.edit_text(
            "⚠️ Hubo un error de conexión con la IA. "
            "Por favor, intentá de nuevo."
        )

        return

    especialidad = datos.get(
        "especialidad"
    )

    clinica = datos.get(
        "clinica"
    )

    duda = datos.get(
        "duda_extra"
    )

    print("\n======================================")
    print("🧠 DATOS INTERPRETADOS")
    print("======================================")
    print(f"Especialidad: {especialidad}")
    print(f"Clínica: {clinica}")
    print(f"Duda extra: {duda}")
    print("======================================\n")

    # --------------------------------------------------------
    # 2. Crear solicitud de turno
    # --------------------------------------------------------

    if especialidad and clinica:

        res_solicitud = ips_mock.crear_solicitud(
            chat_id,
            especialidad,
            clinica,
            nombre_usuario
        )

        if res_solicitud.get("ok"):

            solicitud_id = (
                res_solicitud[
                    "solicitud_id"
                ]
            )

            await msg_espera.edit_text(
                "✅ ¡Entendido! No hay turnos "
                "disponibles ahora mismo.\n\n"

                "👀 <b>He activado la Vigilancia "
                "Asíncrona.</b>\n\n"

                "Me quedaré monitoreando el sistema "
                "del IPS por vos. Podés cerrar Telegram "
                "tranquilamente y te aviso apenas "
                "aparezca un turno liberado.",

                parse_mode=constants.ParseMode.HTML
            )

            asyncio.create_task(
                vigilar_turnos(
                    chat_id,
                    solicitud_id,
                    context
                )
            )

        else:

            await msg_espera.edit_text(
                "⚠️ Hubo un problema al crear "
                "la solicitud."
            )

    else:

        await msg_espera.edit_text(
            "⚠️ No pude identificar completamente "
            "la especialidad médica o la clínica.\n\n"

            "Por ejemplo podés decir:\n"
            "\"Necesito pediatría en IPS Ingavi.\""
        )

    # --------------------------------------------------------
    # 3. Procesar duda adicional
    # --------------------------------------------------------

    if duda:

        mensaje_busqueda = (
            await update.message.reply_text(
                "🔎 Buscando información oficial "
                "del IPS..."
            )
        )

        # Exa recupera información.
        resultados_exa = await buscar_info_exa(
            duda=duda,
            especialidad=especialidad,
            clinica=clinica
        )

        if not resultados_exa:

            await mensaje_busqueda.edit_text(
                "🔎 No encontré información oficial "
                "suficiente del IPS para responder "
                "esa consulta."
            )

            return

        # OpenAI convierte las fuentes en una respuesta.
        respuesta_final = await responder_duda_ips(
            pregunta=duda,
            especialidad=especialidad,
            clinica=clinica,
            resultados_exa=resultados_exa
        )

        # Escapamos el texto porque Telegram usará HTML.
        respuesta_segura = html.escape(
            respuesta_final
        )

        # Sacamos algunas fuentes para mostrarlas abajo.
        fuentes = []

        for resultado in resultados_exa[:2]:

            url = resultado.get("url")

            if url:
                fuentes.append(url)

        texto_fuentes = ""

        if fuentes:

            texto_fuentes = (
                "\n\n<b>Fuentes oficiales consultadas:</b>"
            )

            for numero, url in enumerate(
                fuentes,
                start=1
            ):

                url_segura = html.escape(
                    url,
                    quote=True
                )

                texto_fuentes += (
                    f'\n<a href="{url_segura}">'
                    f"Fuente {numero}</a>"
                )

        mensaje_final = (
            "🔎 <b>Sobre tu consulta:</b>\n\n"
            f"{respuesta_segura}"
            f"{texto_fuentes}"
        )

        # Seguridad adicional por límite de Telegram.
        if len(mensaje_final) > 3900:

            mensaje_final = (
                mensaje_final[:3800]
                + "\n\n..."
            )

        await mensaje_busqueda.edit_text(
            mensaje_final,
            parse_mode=constants.ParseMode.HTML,
            disable_web_page_preview=True
        )


# ============================================================
# MANEJO GLOBAL DE ERRORES
# ============================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logging.exception(
        "Error procesando actualización:",
        exc_info=context.error
    )


# ============================================================
# INICIO
# ============================================================

if __name__ == "__main__":

    TOKEN = os.getenv(
        "TELEGRAM_TOKEN"
    )

    if not TOKEN:

        print(
            "❌ ERROR CRÍTICO: "
            "No se encontró TELEGRAM_TOKEN "
            "en el archivo .env"
        )

        raise SystemExit(1)

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    app.add_handler(
        CommandHandler(
            "cancelar",
            cancelar_command
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    app.add_error_handler(
        error_handler
    )

    print(
        "🚀 Bot Mi turno IPS ensamblado."
    )

    print(
        "🤖 OpenAI: listo"
    )

    print(
        "🔎 Exa: listo"
    )

    print(
        "👀 Vigilancia de turnos: lista"
    )

    print(
        "📲 Escuchando mensajes de Telegram...\n"
    )

    app.run_polling()