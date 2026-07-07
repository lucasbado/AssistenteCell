Sempre priorize:
- baixo acoplamento
- alta coesão
- separação de responsabilidades
- facilidade de testes
- extensibilidade
- processamento assíncrono
- consumo mínimo de CPU/RAM
- reutilização
- eventos imutáveis
- componentes independentes

Se perceber alguma arquitetura melhor do que a atual, explique os benefícios e proponha a mudança.

Nunca mantenha uma arquitetura apenas por compatibilidade se existir uma solução claramente superior.

--------------------------------------------
VISÃO GERAL DO PROJETO
--------------------------------------------

Estamos desenvolvendo uma Assistente Cognitiva Pessoal totalmente local.

O objetivo NÃO é criar um chatbot.

O objetivo é construir um sistema semelhante a um cérebro artificial dividido em pequenas especializações.

A IA (LLM) é apenas um componente do sistema.

Ela nunca será responsável por toda a inteligência.

A inteligência deverá ser distribuída entre diversos agentes especializados.

--------------------------------------------
FILOSOFIA DO PROJETO
--------------------------------------------

O sistema deverá funcionar como um cérebro.

As camadas devem seguir aproximadamente esta ordem:

Sensores
↓

Filtro de Atenção

↓

Memória de Trabalho

↓

Reflexos

↓

Inferência

↓

Memória Semântica

↓

Cognição (LLM)

↓

Planejamento

↓

Execução

↓

Aprendizado

A LLM representa apenas o "córtex".

Todo o restante deve funcionar sem depender dela.

O objetivo é que mais de 90% dos eventos nunca precisem chegar na LLM.

--------------------------------------------
ARQUITETURA GERAL
--------------------------------------------

O sistema será dividido em dois polos.

### Android

Responsável apenas por perceber acontecimentos.

Ele nunca faz processamento pesado.

Ele envia eventos.

Ele recebe ações.

Nada mais.

Sensores utilizados:

- NotificationListener
- UsageStats
- Accessibility
- Broadcast Receivers
- Intent Receivers
- Futuramente sensores físicos

Todos os eventos são enviados ao servidor.

--------------------------------------------

### PC

Todo processamento ocorre aqui.

Tecnologias:

Python

FastAPI

SQLite

Ollama

CUDA (RTX 4060)

Future:
Redis
Banco Vetorial

--------------------------------------------
HARDWARE
--------------------------------------------

Ryzen 7 5700X3D

32GB RAM

RTX 4060 8GB

Windows 11

--------------------------------------------
PRINCÍPIOS DA ARQUITETURA
--------------------------------------------

Nunca criar lógica de negócio dentro do Kernel.

O Kernel é completamente burro.

Ele apenas recebe eventos.

Aplica filtros.

Despacha eventos.

Nada mais.

Toda inteligência pertence aos agentes.

Cada agente deve possuir apenas uma responsabilidade.

Novos agentes devem poder ser adicionados sem alterar o Kernel.

--------------------------------------------
EVENTO CANÔNICO
--------------------------------------------

Todo o sistema conversa utilizando apenas um único tipo de evento.

EventoCanonico

Todos os módulos devem utilizar esse contrato.

Os eventos são imutáveis.

Nenhum agente altera um evento existente.

Sempre gera um clone.

Todo evento possui rastreabilidade completa através de:

- id
- correlacao_id
- evento_pai

--------------------------------------------
PIPELINE COGNITIVO
--------------------------------------------

Sensor

↓

Pipeline de Atenção

↓

Kernel

↓

Agentes

↓

Novos Eventos

↓

Kernel

↓

...

Os agentes nunca chamam outros agentes diretamente.

Toda comunicação acontece apenas através do Kernel.

--------------------------------------------
SISTEMA DE ATENÇÃO
--------------------------------------------

Antes de qualquer agente executar existe um Pipeline de Atenção.

Ele decide:

score de atenção

relevância

spam

duplicação

cooldown

novidade

prioridade

contexto

Somente eventos aprovados entram no Kernel.

--------------------------------------------
MEMÓRIAS
--------------------------------------------

Existem diferentes tipos de memória.

Memória de Trabalho

Memória Episódica

Memória Semântica

Perfil do Usuário

Estatísticas

Cada memória possui responsabilidades diferentes.

--------------------------------------------
AGENTES
--------------------------------------------

Os agentes representam especializações.

Exemplos:

Agente Música

Agente Mensagens

Agente Hábitos

Agente Perfil

Agente Reflexo

Agente Inferência

Agente Cognição

Agente Planejamento

Agente Execução

Agente Memória

Cada agente produz novos eventos.

Nunca executa diretamente outro agente.

--------------------------------------------
LLM
--------------------------------------------

A LLM deve ser utilizada apenas quando realmente necessário.

Ela funciona como um especialista.

Nunca como controlador do sistema.

Ela recebe:

evento

contexto

memória

histórico

E devolve somente decisões estruturadas.

Preferencialmente JSON.

--------------------------------------------
OBJETIVO FINAL
--------------------------------------------

Queremos construir um sistema cognitivo modular que possa crescer durante anos.

O projeto deve lembrar mais um sistema operacional cognitivo do que um chatbot.

Cada novo recurso deve surgir através da criação de novos agentes, nunca através do aumento de um único arquivo gigantesco.

Sempre que responder:

1. Pense primeiro na arquitetura.

2. Depois proponha melhorias.

3. Só então escreva código.

4. Sempre prefira componentes pequenos e especializados.

5. Sempre preserve baixo acoplamento e alta escalabilidade.

6. Caso exista uma solução arquitetural melhor, proponha-a mesmo que exija refatoração.

Considere este contexto como a documentação oficial do projeto durante toda a conversa.