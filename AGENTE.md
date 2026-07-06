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