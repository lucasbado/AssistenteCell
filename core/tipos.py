from enum import Enum

class CategoriaEvento(str, Enum):
    MEDIA = "MEDIA"
    APP_FOREGROUND = "APP_FOREGROUND"

class TipoAcao(str, Enum):
    INTENCAO_INTERACAO = "INTENCAO_INTERACAO"
    EVENTO_COMPLEXO = "EVENTO_COMPLEXO"

class PrioridadeEvento(int, Enum):
    BAIXO = 1
    MEDIUM = 2
    ALTO = 3

class OrigemEvento(str, Enum):
    KERNEL = "KERNEL"
    AGENTE = "AGENTE"

class EstadoEvento(str, Enum):
    PENDENTE = "PENDENTE"
    PROCESSADO = "PROCESSADO"

class TipoEntidade(str, Enum):
    ARTISTA = "ARTISTA"
    APP = "APP"
    CONTATO = "CONTATO"
