# Evento Canônico

Todo componente conversa utilizando apenas EventoCanonico.

Nunca utilizar DTOs diferentes.

---

## Estrutura

id

correlation_id

parent_event

timestamp

origem

tipo

payload

metadata

attention_score

priority

---

## Regras

Eventos são imutáveis.

Nunca alterar um evento.

Sempre gerar novo evento.

Todo evento deve possuir rastreabilidade completa.

Todo evento possui apenas um responsável por produzi-lo.

Eventos representam fatos ocorridos.

Nunca comandos.

Nunca chamadas diretas.

Sempre fatos.