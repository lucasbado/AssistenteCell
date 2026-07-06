from enum import Enum

class CategoriaEvento(str, Enum):
    MEDIA = "MEDIA"
    APP_FOREGROUND = "APP_FOREGROUND"

class TipoAcao(str, Enum):
    INTENCAO_INTERACAO = "INTENCAO_INTERACAO"
    EVENTO_COMPLEXO = "EVENTO_COMPLEXO"

class PrioridadeEvento(int, Enum):
    BAIXA = 1
    NORMAL = 2
    ALTA = 3

class OrigemEvento(str, Enum):
    KERNEL = "KERNEL"
    USUARIO = "USUARIO"

class EstadoEvento(str, Enum):
    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDO = "CONCLUIDO"

class TipoEntidade(str, Enum):
    ARTISTA = "ARTISTA"
    APP = "APP"
    CONTATO = "CONTATO"
