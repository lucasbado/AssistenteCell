"""
servicos/llm.py

Único ponto do sistema autorizado a conversar com a LLM.

Objetivos:

- Centralizar prompts
- Timeout
- Retry
- Configurações do modelo
- Futuramente streaming
- Futuramente fallback de modelos
"""

from __future__ import annotations

import json
import logging
import requests

from modelos.catalogo import EntidadeSemantica

logger = logging.getLogger(__name__)


class ServicoLLM:

    def __init__(self):

        self.url = "http://localhost:11434/api/generate"

        self.modelo = "qwen2.5:7b"

        self.timeout = 30

    # =====================================================
    # API PRIVADA
    # =====================================================

    def _gerar_json(
        self,
        prompt: str,
        system: str,
    ) -> dict:

        payload = {

            "model": self.modelo,

            "prompt": prompt,

            "system": system,

            "stream": False,

            "format": "json",

            "options": {

                "temperature": 0.2,

                "num_ctx": 2048,

            },
        }

        resposta = requests.post(

            self.url,

            json=payload,

            timeout=self.timeout,

        )

        resposta.raise_for_status()

        texto = resposta.json()["response"]

        return json.loads(texto)

    # =====================================================
    # ARTISTAS
    # =====================================================

    async def classificar_artista(
        self,
        nome: str,
    ) -> EntidadeSemantica:

        system = """
Você é um catálogo musical.

Responda APENAS JSON.

Esquema:

{
    "tipo":"ARTISTA",
    "chave":"",
    "atributos":{

        "genero":"",

        "pais":"",

        "epoca":"",

        "similar":[]
    }
}
"""

        prompt = f"Artista: {nome}"

        dados = self._gerar_json(prompt, system)

        return EntidadeSemantica.model_validate(dados)

    # =====================================================
    # APPS
    # =====================================================

    async def classificar_app(
        self,
        pacote: str,
    ) -> EntidadeSemantica:

        system = """Você classifica aplicativos Android a partir do nome do pacote.

O atributo "nome" deve ser o nome de exibição do aplicativo (ex: "WhatsApp", "Instagram").
O atributo "chave" deve ser o próprio nome do pacote.

Responda apenas JSON.

{
    "tipo":"APP",
    "chave":"com.exemplo.app",
    "atributos":{
        "nome": "Nome do App",
        "categoria":"Produtividade",
        "descricao":"Breve descrição do que o app faz."
    }
}
"""

        prompt = f"Pacote Android: {pacote}"

        dados = self._gerar_json(prompt, system)

        # Garante que a chave seja o pacote, caso a LLM não o faça.
        dados['chave'] = pacote

        return EntidadeSemantica.model_validate(dados)
    
    async def classificar_evento(
        self,
        categoria: str,
        pacote: str,
        payload: dict,
    ) -> dict:
        """
        Classifica um evento e retorna um JSON com:
        - categoria_inferida: str
        - mensagem_dinamica: str | None
        - acao_necessaria: bool
        - contexto_extra: dict (opcional)
        """
        system = """Você é o módulo de Cognição da assistente Ollie.

Você recebe apenas eventos que os módulos de Atenção e Reflexo NÃO conseguiram resolver.

Sua função NÃO é decidir políticas do sistema.
Sua função é apenas interpretar linguagem humana e gerar uma resposta estruturada.

O evento recebido possui:

- categoria: tipo do evento
- pacote: aplicativo de origem
- payload: dados estruturados do evento

Analise apenas o payload recebido.

### Regras

NOTIFICACAO
- O campo "titulo" normalmente representa o remetente.
- O campo "texto" representa o conteúdo.
- Preserve as informações importantes.
- Nunca invente nomes.
- Nunca invente mensagens.
- Não resuma demais quando a mensagem for curta.
- Se houver emojis, pode ignorá-los.

MEDIA
- Utilize artista, música, álbum ou vídeo quando disponíveis.

APP_FOREGROUND
- Interprete o aplicativo aberto e o possível contexto.

Se não houver informação suficiente para criar uma mensagem útil,
retorne: "acao_necessaria": false

Se você precisar de informações externas (da internet) para responder,
retorne: "contexto_extra": {"precisa_pesquisar": true, "query": "sua pergunta aqui"}
e "acao_necessaria": false.

Nunca invente dados.

Retorne SOMENTE JSON válido.

Formato:
{
    "categoria_inferida": "...",
    "confianca": 0.0,
    "acao_necessaria": true,
    "mensagem_dinamica": "...",
    "contexto_extra": {}
}"""
        prompt = json.dumps({"categoria": categoria, "pacote": pacote, "payload": payload}, ensure_ascii=False, indent=2)

        try:
            dados = self._gerar_json(prompt, system)
            # Garante que os campos obrigatórios existam
            dados.setdefault("categoria_inferida", "DESCONHECIDA")
            dados.setdefault("confianca", 0.0)
            dados.setdefault("mensagem_dinamica", None)
            dados.setdefault("acao_necessaria", False)
            dados.setdefault("contexto_extra", {})
            return dados
        except Exception as e:
            logger.error(f"Erro ao classificar evento: {e}")
            # Fallback seguro: não age
            return {
                "categoria_inferida": "ERRO",
                "confianca": 0.0,
                "mensagem_dinamica": None,
                "acao_necessaria": False,
                "contexto_extra": {"erro": str(e)}
            }

    async def resumir_perfil_usuario(self, dados_perfil_texto: str) -> dict:
        """
        Recebe uma lista de fatos sobre o usuário e gera um resumo em linguagem natural.
        """
        system = """Você é um psicólogo e analista de comportamento.
Sua tarefa é analisar uma lista de fatos brutos sobre um usuário e criar um resumo conciso e perspicaz sobre seus hábitos e personalidade.

Seja direto e informativo. Use um tom amigável.
O objetivo é mostrar ao usuário o que o sistema aprendeu sobre ele.

Responda APENAS com um JSON no seguinte formato:
{
    "resumo": "..."
}"""
        prompt = f"""
Analise os seguintes fatos sobre o usuário e crie um resumo:

{dados_perfil_texto}
"""
        try:
            dados = self._gerar_json(prompt, system)
            dados.setdefault("resumo", "Não foi possível gerar um resumo no momento.")
            return dados
        except Exception as e:
            logger.error(f"Erro ao resumir perfil de usuário: {e}")
            return {"resumo": f"Ocorreu um erro ao tentar analisar o perfil: {e}"}

    # =====================================================
    # CONTATOS
    # =====================================================

    async def classificar_contato(
        self,
        nome: str,
    ) -> EntidadeSemantica:

        return EntidadeSemantica(

            tipo="CONTATO",

            chave=nome,

            atributos={

                "nome": nome

            }

        )

    # =====================================================
    # CLASSIFICAÇÃO GENÉRICA
    # =====================================================

    async def classificar_generico(

        self,

        tipo: str,

        chave: str,

        schema: dict,

    ) -> dict:

        system = f"""
Você responde apenas JSON.

Tipo:

{tipo}

Esquema esperado:

{json.dumps(schema, indent=4)}
"""

        prompt = chave

        return self._gerar_json(

            prompt,

            system,

        )