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
import os

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

    def _carregar_instrucoes_cognitivas(self) -> str:
        """
        Carrega o manifesto de capacidades e as regras de identidade do córtex.
        Fonte da verdade: Documentação do projeto Android.
        """
        try:
            # Caminho absoluto conforme definido no plano de implementação
            base_path = "D:/Programacao/Projetos/AssistenteCell/app/src/docs"
            
            with open(os.path.join(base_path, "capabilities.md"), "r", encoding="utf-8") as f:
                capabilities = f.read()
            
            with open(os.path.join(base_path, "llm.md"), "r", encoding="utf-8") as f:
                llm_rules = f.read()
                
            return f"\n--- MANIFESTO DE CAPACIDADES ---\n{capabilities}\n\n--- REGRAS DE IDENTIDADE ---\n{llm_rules}\n"
        except Exception as e:
            logger.warning(f"Não foi possível carregar instruções cognitivas: {e}")
            return ""

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
        instrucoes_extras = self._carregar_instrucoes_cognitivas()
        
        system_base = """Você é o módulo de Cognição da assistente Ollie. Sua função é interpretar eventos e gerar uma resposta ESTRUTURADA em JSON.

### INSTRUÇÕES COGNITIVAS ADICIONAIS
{instrucoes}

Você recebe eventos que as camadas de Atenção e Reflexo não resolveram. O evento tem `categoria`, `pacote` e `payload`.

### Nuances Culturais (Português do Brasil)
- **CUIDADO COM LITERALIDADE**: Muitas expressões são idiomáticas. Antes de classificar algo como urgente ou um pedido de ajuda, analise o contexto.
- **Exemplo de Ambiguidade**: A frase "isso ajuda demais" é um ELOGIO (significa "isso é muito útil/bom"), e **NÃO** um pedido de socorro.
- **Tom da Conversa**: Avalie o tom geral da conversa (presente no `contexto_historico`) para entender a real intenção por trás das mensagens. Não isole palavras.

### Regras de Prioridade
- **ALTA**: Mensagens diretas de uma pessoa (ex: WhatsApp, SMS de um contato). Notificações urgentes (ex: calendário, lembretes).
- **NORMAL**: Mensagens de grupo. E-mails importantes. Notificações de apps de produtividade.
- **BAIXA**: Notificações de redes sociais (likes, novos posts), promoções, notícias não urgentes.

### Regra de Interação (O mais importante!)
Sua principal decisão é o "tipo_interacao", mas você também pode (e deve) emitir uma "decisao" estruturada se identificar uma oportunidade de automação conforme o manifesto de capacidades.

- **NOTIFICAR**: Use quando for a primeira vez que você vê um assunto, ou se uma informação MUITO importante e nova chegou.
- **DECISAO_COGNITIVA**: Use quando você decidir agir no sistema (ex: ativar um perfil de foco, sugerir uma rotina). Você pode combinar isso com uma notificação.
- **ATUALIZACAO_SILENCIOSA**: Use se as novas mensagens são apenas uma continuação de um tópico que você já resumiu nos últimos minutos.

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
{{
    "categoria_inferida": "MENSAGEM_PESSOAL",
    "confianca": 0.9,
    "prioridade": "ALTA",
    "tipo_interacao": "NOTIFICAR",
    "mensagem_dinamica": "Resumo da situação para o usuário.",
    "contexto_extra": {{}},
    "acao_sugerida": {{
        "tipo": "OPEN_APP",
        "parametro": "com.whatsapp",
        "texto_botao": "Abrir WhatsApp"
    }}
}}"""
        system = system_base.replace("{instrucoes}", instrucoes_extras)
        
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
        Recebe uma lista de fatos sobre o usuário e gera uma lista de cards dinâmicos.
        """
        instrucoes_extras = self._carregar_instrucoes_cognitivas()
        
        system_base = """Você é um assistente pessoal proativo e perspicaz chamado Ollie.
Sua tarefa é analisar fatos sobre o uso do celular de um usuário e gerar uma LISTA de cards dinâmicos para a tela inicial.

### INSTRUÇÕES CRÍTICAS
1. **NÃO USE PORCENTAGENS OU ESTATÍSTICAS TÉCNICAS.** O usuário quer auxílio e contexto, não um relatório de BI.
2. **FOQUE NO AUXÍLIO**: Como esse dado ajuda o usuário? O que ele pode fazer com isso?
3. **TOM DE VOZ**: Amigável, conciso e observador.
4. **FORMATO**: Gere uma lista de objetos, cada um com um "tipo" (insight, dica, piada) e "conteudo".

### TIPOS DE CARDS
- **insight**: Observações sobre padrões de comportamento (ex: "Você parece mais produtivo após ouvir música clássica").
- **dica**: Sugestões acionáveis ou lembretes de bem-estar (ex: "Que tal uma pausa de 5 minutos para alongar?").
- **piada**: Uma piada curta e leve relacionada a tecnologia ou ao dia a dia.

### EXEMPLO DE RESPOSTA ESPERADA
{{
    "cards": [
        {{
            "tipo": "insight",
            "conteudo": {{
                "title": "Foco & Música",
                "text": "Percebi que seu fluxo de trabalho no VS Code melhora quando você ouve Lo-fi. Quer que eu prepare o ambiente?"
            }}
        }},
        {{
            "tipo": "dica",
            "conteudo": {{
                "title": "Pausa Necessária",
                "text": "Você está focado no WhatsApp há algum tempo. Uma breve caminhada pode te ajudar a clarear as ideias."
            }}
        }},
        {{
            "tipo": "piada",
            "conteudo": {{
                "text": "Por que o computador foi ao médico? Porque ele estava com um vírus de 'macro' proporções!"
            }}
        }}
    ]
}}

### INSTRUÇÕES COGNITIVAS ADICIONAIS
{instrucoes}

Responda APENAS com um JSON válido seguindo a estrutura acima."""
        system = system_base.replace("{instrucoes}", instrucoes_extras)

        prompt = f"""
Analise os seguintes fatos sobre o usuário e gere os cards:

{dados_perfil_texto}
"""
        try:
            dados = await self._gerar_json(prompt, system)
            if "cards" not in dados or not isinstance(dados["cards"], list):
                # Fallback se a LLM não seguir o formato de lista
                resumo_texto = dados.get("resumo", "Sem insights no momento.")
                return {
                    "cards": [
                        {
                            "tipo": "insight",
                            "conteudo": {"title": "Observação", "text": resumo_texto}
                        }
                    ]
                }
            return dados
        except Exception as e:
            logger.error(f"Erro ao gerar cards de perfil: {e}")
            return {
                "cards": [
                    {
                        "tipo": "insight",
                        "conteudo": {"text": "Estou observando seus padrões para te ajudar melhor em breve."}
                    }
                ]
            }

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