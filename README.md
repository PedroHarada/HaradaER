# HaradaER

Ferramenta de modelagem Entidade-Relacionamento em Python, compatível com o arquivo `.xml` do
TerraER 3.14: um modelo salvo no HaradaER abre no TerraER com o mesmo
diagrama, e o inverso também vale.

Estado: em construção (marco M0, esqueleto do projeto). Nada utilizável ainda.

## Documentação

- [Requisitos](docs/REQUISITOS.md)
- [Arquitetura e design](docs/ARQUITETURA.md)
- [Investigações sobre o TerraER](docs/INVESTIGACOES.md)

## Desenvolvimento

Alvo da v1: Linux (Wayland), Python 3.14 e PySide6 6.12.

```
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/ruff check .
```

O `TerraER3.14.jar` é só material de consulta e não faz parte do repositório (está no `.gitignore`).
