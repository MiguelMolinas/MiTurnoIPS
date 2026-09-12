import os
import asyncio
from typing import Any


<<<<<<< HEAD
def find_requirements(query: str) -> list[dict[str, Any]]:
    """Busca requisitos con contenido destacado cuando Exa está configurado.

    La integración queda aislada para poder incorporarla al flujo de bot sin
    acoplar las credenciales ni el cliente externo al resto de la aplicación.
=======
async def buscar_info_exa(
    duda: str,
    especialidad: str | None = None,
    clinica: str | None = None
) -> list[dict[str, Any]]:
>>>>>>> 03b8a44 (Feature All)
    """
    Busca información oficial del IPS mediante Exa.

    Devuelve resultados estructurados.
    NO genera texto para Telegram.
    """

    api_key = os.getenv("EXA_API_KEY")

    if not api_key:
        print("❌ Falta EXA_API_KEY en el archivo .env")
        return []

    consulta = _crear_consulta(
        duda=duda,
        especialidad=especialidad,
        clinica=clinica
    )

    try:
        resultados = await asyncio.to_thread(
            _realizar_busqueda_exa,
            api_key,
            consulta
        )

        return resultados

    except Exception as e:
        print(f"❌ ERROR CONSULTANDO A EXA: {e}")
        return []


def _crear_consulta(
    duda: str,
    especialidad: str | None,
    clinica: str | None
) -> str:
    """
    Genera una consulta específica para evitar resultados irrelevantes.
    """

    partes = [
        "Instituto de Previsión Social IPS Paraguay"
    ]

    if clinica:
        partes.append(f"sede {clinica}")

    if especialidad:
        partes.append(f"especialidad {especialidad}")

    partes.append(duda)

    # Agregamos términos que ayudan cuando la consulta trata
    # sobre atención médica y requisitos.
    partes.append(
        "requisitos documentos necesarios atención asegurado"
    )

    return ". ".join(partes)


def _realizar_busqueda_exa(
    api_key: str,
    query: str
) -> list[dict[str, Any]]:
    """
    Función síncrona que realiza la búsqueda con Exa.
    Se ejecuta desde asyncio.to_thread().
    """

    from exa_py import Exa

<<<<<<< HEAD
    results = Exa(api_key).search(
        query,
        type="auto",
        num_results=20,
        contents={"highlights": True},
        include_domains=["IPS2.vercel.app"],
    )
    return [
        {
            "title": result.title or "Sin título",
            "url": result.url,
            "highlights": result.highlights or [],
        }
        for result in results.results
    ]
=======
    exa = Exa(api_key)

    print("\n======================================")
    print("🔎 CONSULTANDO EXA")
    print("======================================")
    print(f"Consulta: {query}")

    results = exa.search(
        query,
        type="auto",
        num_results=5,

        # Solo resultados oficiales del IPS.
        include_domains=[
            "ips.gov.py"
        ],

        contents={
            "highlights": True
        }
    )

    print(f"\nResultados encontrados: {len(results.results)}")

    resultados = []

    for result in results.results:

        titulo = result.title or "Instituto de Previsión Social"
        url = result.url or ""
        highlights = result.highlights or []

        print("--------------------------------------")
        print(f"TÍTULO: {titulo}")
        print(f"URL: {url}")
        print(f"FRAGMENTOS: {len(highlights)}")

        # Limitamos el contenido que después recibirá OpenAI.
        fragmentos_limpios = []

        for fragmento in highlights[:3]:

            if not fragmento:
                continue

            fragmento = fragmento.strip()

            # Evita mandar textos gigantes al modelo.
            if len(fragmento) > 1500:
                fragmento = fragmento[:1500]

            fragmentos_limpios.append(fragmento)

        resultados.append(
            {
                "titulo": titulo,
                "url": url,
                "fragmentos": fragmentos_limpios
            }
        )

    print("======================================\n")

    return resultados
>>>>>>> 03b8a44 (Feature All)
