"""
core/tipos.py

Enums oficiais utilizados pelo Kernel Cognitivo.

Nunca utilizar strings "soltas" dentro do sistema.
Todo roteamento deverá utilizar estes tipos.
"""

from enum import Enum


class CategoriaEvento(str, Enum):
    """A natureza do evento, o que aconteceu no mundo exterior."""
    MEDIA = "MEDIA"
    NOTIFICACAO = "NOTIFICACAO"
    APP_FOREGROUND = "APP_FOREGROUND"
    SISTEMA = "SISTEMA"
    WEB = "WEB"
    PERFIL = "PERFIL"
    COMANDO = "COMANDO"

class TipoAcao(str, Enum):
    """O que fazer com o evento, qual o próximo passo no pipeline."""
    NORMAL = "NORMAL"                         # Estado inicial
    EVENTO_COMPLEXO = "EVENTO_COMPLEXO"       # Sinaliza que um agente não soube o que fazer
    INTENCAO_RACIOCINIO = "INTENCAO_RACIOCINIO" # Intenção de usar a LLM
    INTENCAO_INTERACAO = "INTENCAO_INTERACAO"  # Intenção de notificar o usuário

class PrioridadeEvento(int, Enum):
    """
    Prioridade de processamento.

    Futuramente poderá ser utilizada
    por múltiplas filas ou scheduler.
    """

    BAIXA = 10

    NORMAL = 50

    ALTA = 80

    CRITICA = 100


class OrigemEvento(str, Enum):
    """
    Quem criou o evento.
    """

    ANDROID = "ANDROID"

    WINDOWS = "WINDOWS"

    IA = "IA"

    SCRAPING = "SCRAPING"

    SISTEMA = "SISTEMA"

    USUARIO = "USUARIO"


class EstadoEvento(str, Enum):
    """
    Estado atual do processamento.
    """

    NOVO = "NOVO"

    EM_PROCESSAMENTO = "EM_PROCESSAMENTO"

    PROCESSADO = "PROCESSADO"

    CANCELADO = "CANCELADO"

    ERRO = "ERRO"


class TipoEntidade(str, Enum):

    ARTISTA = "ARTISTA"

    APP = "APP"

    CONTATO = "CONTATO"

    BANDA = "BANDA"

    GENERO = "GENERO"

    FILME = "FILME"

    LIVRO = "LIVRO"

    LOCAL = "LOCAL"

    PESSOA = "PESSOA"

    SITE = "SITE"
