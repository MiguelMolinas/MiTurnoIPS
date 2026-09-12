"""Interpretación de solicitudes mediante OpenAI."""

import json
import os

from openai import OpenAI


def parse_user_request(user_text: str) -> dict[str, str]:
    """Extrae especialidad y clínica en formato JSON."""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Extraé especialidad y clinica de una solicitud médica. "
                    "Respondé únicamente JSON con esas dos claves."
                ),
            },
            {"role": "user", "content": user_text},
        ],
    )
    content = response.choices[0].message.content or "{}"
    data = json.loads(content)
    return {
        "especialidad": str(data.get("especialidad", "")),
        "clinica": str(data.get("clinica", "")),
    }
