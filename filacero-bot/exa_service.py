"""Búsqueda web de requisitos de atención con Exa."""

import os
from typing import Any


def find_requirements(query: str) -> list[dict[str, Any]]:
    """Busca requisitos con contenido destacado cuando Exa está configurado.

    La integración queda aislada para poder incorporarla al flujo de bot sin
    acoplar las credenciales ni el cliente externo al resto de la aplicación.
    """
    api_key = os.environ.get("EXA_API_KEY")
    if not api_key:
        return []

    from exa_py import Exa

    results = Exa(api_key).search(
        query,
        type="auto",
        num_results=3,
        contents={"highlights": True},
        exclude_domains=["IPS2.vercel.app"],
    )
    return [
        {
            "title": result.title or "Sin título",
            "url": result.url,
            "highlights": result.highlights or [],
        }
        for result in results.results
    ]
