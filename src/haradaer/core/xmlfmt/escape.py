"""Escape de texto como o TerraER faz.

Regras medidas no TerraER 3.14 (`docs/INVESTIGACOES.md`):
- `& < > " '` viram `&amp; &lt; &gt; &quot; &apos;`;
- `\\n` fica literal;
- qualquer outro caractere abaixo de 0x20, ou a partir de 0x7f, vira `&#x<hex minúsculo>;`;
- caracteres fora do plano básico (acima de 0xFFFF, como emojis) viram **dois** pedaços
  substitutos (`&#xd83d;&#xde00;`), porque o leitor do TerraER corrompe `&#x1f600;`.
"""

_BASICOS = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;"}


def escape(texto: str) -> str:
    saida: list[str] = []
    for caractere in texto:
        basico = _BASICOS.get(caractere)
        if basico is not None:
            saida.append(basico)
            continue
        codigo = ord(caractere)
        if caractere == "\n" or 0x20 <= codigo < 0x7F:
            saida.append(caractere)
        elif codigo > 0xFFFF:
            codigo -= 0x10000
            saida.append(f"&#x{0xD800 + (codigo >> 10):x};&#x{0xDC00 + (codigo & 0x3FF):x};")
        else:
            saida.append(f"&#x{codigo:x};")
    return "".join(saida)
