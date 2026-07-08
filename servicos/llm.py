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

import httpx
from modelos.catalogo import EntidadeSemantica

logger = logging.getLogger(__name__)


class ServicoLLM:

    def __init__(self):

        self.url = "http://localhost:11434/api/generate"

        self.modelo = "qwen2.5:7b"
        self.timeout = 30
        # Use um cliente assíncrono para não bloquear o event loop.
        self.client = httpx.AsyncClient(timeout=self.timeout)

    # =====================================================
    # API PRIVADA
    # =====================================================

    async def _gerar_json(
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

        resposta = await self.client.post(self.url, json=payload)
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

        dados = await self._gerar_json(prompt, system)

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

        dados = await self._gerar_json(prompt, system)

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
        - mensagem_dinamica: str
        - acao_necessaria: bool
        - contexto_extra: dict (opcional)
        """
        system = """Você é o módulo de Cognição da assistente Ollie. Sua função é interpretar eventos e gerar uma resposta ESTRUTURADA em JSON.

Você recebe eventos que as camadas de Atenção e Reflexo não resolveram. O evento tem `categoria`, `pacote` e `payload`.

### Regras de Prioridade
- **ALTA**: Mensagens diretas de uma pessoa (ex: WhatsApp, SMS de um contato). Notificações urgentes (ex: calendário, lembretes).
- **NORMAL**: Mensagens de grupo. E-mails importantes. Notificações de apps de produtividade.
- **BAIXA**: Notificações de redes sociais (likes, novos posts), promoções, notícias não urgentes.

### Regra de Interação (O mais importante!)
Sua principal decisão é o "tipo_interacao".
- **NOTIFICAR**: Use quando for a primeira vez que você vê um assunto, ou se uma informação MUITO importante e nova chegou. Esta ação gera uma notificação para o usuário.
- **ATUALIZACAO_SILENCIOSA**: Use se as novas mensagens são apenas uma continuação de um tópico que você já resumiu nos últimos minutos (presente no "contexto_historico"). O sistema irá absorver a informação sem notificar o usuário, aguardando mais contexto. O objetivo é evitar notificar o usuário a cada 2 minutos sobre a mesma história em andamento.

Se o `pre_resumo` contém "Você tem 12 mensagens...", é um forte indicador para usar "NOTIFICAR".
Se o `pre_resumo` contém "Você tem 2 mensagens..." e o `contexto_historico` mostra que você já notificou sobre isso há pouco tempo, prefira "ATUALIZACAO_SILENCIOSA".

### Regras de Geração da "mensagem_dinamica"
Sua tarefa principal é criar a "mensagem_dinamica". Siga esta hierarquia ESTRITA:

1.  **SE o payload contiver "pre_resumo"**:
    - Este campo é a verdade absoluta, gerado por uma heurística.
    - Sua "mensagem_dinamica" DEVE ser uma versão mais natural e humana DESTE resumo.
    - **NÃO descarte a informação do "pre_resumo".** Por exemplo, se o resumo for "Você tem 2 mensagens de Grupo X e 1 chamada perdida de Maria", sua resposta PODE ser "Olá! Você tem algumas novidades: 2 mensagens do grupo X e uma chamada perdida de Maria.", mas NUNCA "Maria te ligou.".
    - Esta é sua principal fonte de informação. Use-a.

2.  **SENÃO, SE o payload contiver "conversa_completa" ou "mensagens"**:
    - Analise o histórico e as novas mensagens para criar um resumo conciso.

3.  **SENÃO (como último recurso)**:
    - Use "titulo" como remetente e "texto" como a mensagem única para uma notificação simples.

### Regras Adicionais
- Se o payload contiver "contexto_historico", use-o para entender a conversa que aconteceu ANTES das novas mensagens.
- Preserve informações importantes. Não invente nomes ou mensagens.
- Se não houver informação suficiente, retorne "tipo_interacao": "IGNORAR".
- Se precisar de informações da internet, retorne "tipo_interacao": "IGNORAR" e "contexto_extra": {"precisa_pesquisar": true, "query": "sua pergunta aqui"}.

Retorne SOMENTE JSON válido.
Formato:
{
    "categoria_inferida": "MENSAGEM_PESSOAL",
    "confianca": 0.9,
    "prioridade": "ALTA",
    "tipo_interacao": "NOTIFICAR",
    "mensagem_dinamica": "Resumo da situação para o usuário.",
    "contexto_extra": {},
    "acao_sugerida": {
        "tipo": "OPEN_APP",
        "parametro": "com.whatsapp",
        "texto_botao": "Abrir WhatsApp"
    }
}"""
        prompt = json.dumps({"categoria": categoria, "pacote": pacote, "payload": payload}, ensure_ascii=False, indent=2)

        try:
            dados = await self._gerar_json(prompt, system)
            # Garante que os campos obrigatórios existam
            dados.setdefault("categoria_inferida", "DESCONHECIDA")
            dados.setdefault("confianca", 0.0)
            dados.setdefault("mensagem_dinamica", "")
            dados.setdefault("prioridade", "NORMAL") # Fallback de prioridade
            dados.setdefault("tipo_interacao", "IGNORAR") # Fallback seguro
            dados.setdefault("contexto_extra", {})
            dados.setdefault("acao_sugerida", None) # Ação é opcional
            return dados
        except Exception as e:
            logger.error(f"Erro ao classificar evento: {e}")
            # Fallback seguro: não age
            return {
                "categoria_inferida": "ERRO",
                "confianca": 0.0,
                "mensagem_dinamica": "",
                "tipo_interacao": "IGNORAR",
                "prioridade": "NORMAL",
                "contexto_extra": {"erro": str(e)},
                "acao_sugerida": None
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
            dados = await self._gerar_json(prompt, system)
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

        return await self._gerar_json(

            prompt,

            system,

        )