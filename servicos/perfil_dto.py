from pydantic import BaseModel, Field
from typing import List

class HabitoAppDTO(BaseModel):
    """Representa um hábito de uso de aplicativo."""
    nome_app: str
    pacote: str
    categoria: str
    percentual_uso: float = Field(..., description="Percentual de uso em relação ao total de apps observados.")

class PreferenciaMusicalDTO(BaseModel):
    """Representa uma preferência musical."""
    artista: str
    genero: str
    percentual_escuta: float = Field(..., description="Percentual de escuta em relação ao total de artistas observados.")

class PerfilCognitivoDTO(BaseModel):
    """DTO principal para a tela de perfil do usuário."""
    resumo_comportamental: str = Field(..., description="Um resumo em linguagem natural sobre o perfil do usuário, gerado pela IA.")
    habitos_aplicativos: List[HabitoAppDTO] = Field(..., description="Lista dos aplicativos mais utilizados.")
    preferencias_musicais: List[PreferenciaMusicalDTO] = Field(..., description="Lista dos artistas mais ouvidos.")