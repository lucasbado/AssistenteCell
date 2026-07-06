from enum import Enum

class CategoriaEvento(str, Enum):
    MEDIA = "MEDIA"
    APP_FOREGROUND = "APP_FOREGROUND"
    NOTIFICACAO = "NOTIFICACAO"

class TipoAcao(str, Enum):
    NORMAL = "NORMAL"
    INTENCAO_INTERACAO = "INTENCAO_INTERACAO"
    EVENTO_COMPLEXO = "EVENTO_COMPLEXO"
    INTENCAO_RACIOCINIO = "INTENCAO_RACIOCINIO"

class PrioridadeEvento(int, Enum):
    BAIXA = 1
    NORMAL = 2
    ALTA = 3

class OrigemEvento(str, Enum):
    KERNEL = "KERNEL"
    USUARIO = "USUARIO"
    ANDROID = "ANDROID"
    IA = "IA"

class EstadoEvento(str, Enum):
    NOVO = "NOVO"
    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDO = "CONCLUIDO"

class TipoEntidade(str, Enum):
    ARTISTA = "ARTISTA"
    APP = "APP"
    CONTATO = "CONTATO"
