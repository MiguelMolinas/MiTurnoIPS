"""Punto de entrada de FilaCero."""

from bot import build_application


if __name__ == "__main__":
    application = build_application()
    application.run_polling()
