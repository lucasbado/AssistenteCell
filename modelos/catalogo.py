from pydantic import BaseModel, Field

from typing import Any


class EntidadeSemantica(BaseModel):

    tipo: str

    chave: str

    atributos: dict[str, Any] = Field(default_factory=dict)