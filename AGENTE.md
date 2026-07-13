# AssistenteCell

## Objetivo

Você está auxiliando no desenvolvimento do AssistenteCell.

Antes de escrever qualquer código:

1. Analise a arquitetura.
2. Procure violações arquiteturais.
3. Sugira melhorias.
4. Somente então implemente.

---

## Filosofia

A IA não é o centro do sistema.

O sistema é composto por diversos agentes especializados.

A LLM representa apenas um componente cognitivo.

---

## Regras

Nunca:

- colocar lógica no Kernel
- permitir comunicação direta entre agentes
- criar eventos mutáveis
- misturar responsabilidades

Sempre:

- preferir componentes pequenos
- preferir composição à herança
- utilizar processamento assíncrono
- explicar decisões arquiteturais

---

## Documentação

Consulte sempre:

docs/architecture.md
docs/kernel.md
docs/event_model.md
docs/agents.md
docs/memory.md
docs/cognitive_query_layer.md

---

## Camada de Consulta Cognitiva (API Externa)

Enquanto os agentes e o kernel formam o "cérebro" que processa eventos, a Camada de Consulta Cognitiva é a "boca" que comunica o conhecimento adquirido.

### Objetivo

Servir como a única interface entre o backend e o aplicativo cliente (Android). Ela abstrai completamente a complexidade interna do sistema.

### Princípios

- **Abstração Total:** O cliente NUNCA deve saber sobre agentes, memórias ou tabelas de banco de dados.
- **Endpoints de Alto Nível:** Expor endpoints baseados em conceitos, não em dados (`/dashboard`, `/perfil`), em vez de CRUDs (`/get_events`).
- **Transformação de Dados em Narrativa:** A camada é responsável por transformar dados brutos e estatísticas em texto coeso e pronto para exibição. O cliente apenas renderiza.
- **De Dados Brutos a Insights Acionáveis:** A exposição de informações deve priorizar a geração de valor para o usuário.
  - **Resumos Cognitivos:** Não devem ser um relatório do que o sistema sabe ("Eu sei que você gosta de X"), mas sim uma fonte de sugestões e reflexões baseadas nesse conhecimento ("Já que você gosta de X, que tal experimentar Y?"). O objetivo é ser um assistente proativo, não um espião.
  - **Linha do Tempo (Atividade Recente):** Não deve ser um log de eventos de baixo nível (eventos de sistema, notificações brutas). Em vez disso, deve apresentar as "conclusões" e ações de alto nível geradas pelos agentes de IA (ex: "Sugestão musical oferecida", "Resumo de mensagens gerado", "Alerta de bem-estar enviado"). Isso reflete o que o assistente *pensou* e *fez*, não apenas o que ele *viu*.
- **Contratos (DTOs):** A comunicação é feita através de Data Transfer Objects (DTOs) bem definidos, garantindo estabilidade para o cliente mesmo que o backend seja refatorado.

### Arquitetura da Camada

1.  **Endpoints (Routers):** A porta de entrada HTTP.
2.  **Serviços de Consulta:** Orquestram a lógica para construir a resposta de um endpoint.
3.  **Agregadores:** Reúnem e pré-processam dados de diversas fontes internas (memórias, DBs).

Essa separação garante que o sistema possa evoluir em duas frentes independentes: o processamento de eventos em tempo real e a exposição de conhecimento acumulado.