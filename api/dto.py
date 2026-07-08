from pydantic import BaseModel, Field
from typing import List, Union, Literal, Annotated

from servicos.dto import TimelineItemDTO
from api.status import LLMStatusDTO

# --- Definição dos CONTEÚDOS específicos de cada Card ---

class BoasVindasContent(BaseModel):
    """Conteúdo para o card de boas-vindas."""
    titulo: str
    texto: str

class ResumoCognitivoContent(BaseModel):
    """Conteúdo para o card de resumo cognitivo."""
    texto: str

class TimelineContent(BaseModel):
    """Conteúdo para o card de timeline."""
    eventos: List[TimelineItemDTO]

# --- Definição dos CARDS individuais (com 'tipo' literal) ---

class BoasVindasCard(BaseModel):
    tipo: Literal["boas_vindas"] = "boas_vindas"
    conteudo: BoasVindasContent

class ResumoCognitivoCard(BaseModel):
    tipo: Literal["resumo_cognitivo"] = "resumo_cognitivo"
    conteudo: ResumoCognitivoContent

class TimelineCard(BaseModel):
    tipo: Literal["timeline"] = "timeline"
    conteudo: TimelineContent

class StatusLLMCard(BaseModel):
    tipo: Literal["status_llm"] = "status_llm"
    conteudo: LLMStatusDTO # Reutiliza o DTO de status diretamente

# --- União Discriminada de todos os tipos de cards possíveis ---
# O Pydantic usará o campo 'tipo' para validar qual card está sendo usado.
AnyCard = Annotated[
    Union[BoasVindasCard, ResumoCognitivoCard, TimelineCard, StatusLLMCard],
    Field(discriminator="tipo")
]

# --- DTO Principal e final da Home ---

class HomeDTO(BaseModel):
    """
    DTO principal para a tela inicial, baseado em uma lista dinâmica de cards.
    """
    saudacao: str = Field(..., description="Uma saudação personalizada baseada no horário e contexto.")
    cards: List[AnyCard]
