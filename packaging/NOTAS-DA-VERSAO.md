Ferramenta de modelagem Entidade-Relacionamento compatível com o arquivo `.xml` do TerraER 3.14.

## Baixar

| Sistema | Arquivo | Requisitos |
|---|---|---|
| Linux | `HaradaER-…-linux.tar.gz` | Distribuições de 2021 para cá (Ubuntu 22.04+, Arch, Fedora 35+, Mint 21+), 64 bits |
| Windows | `HaradaER-…-windows.zip` | Windows 10 ou 11, 64 bits |
| macOS | `HaradaER-…-macos.zip` | macOS 14 (Sonoma) ou mais novo, chip Apple (M1 em diante) |

Não precisa instalar Python nem nada mais: é só extrair e abrir.

## Como abrir

**Linux:** extraia e rode `./HaradaER` (ou dê dois cliques, se o gerenciador de arquivos permitir).
Em X11 (sem Wayland), se não abrir, instale a biblioteca do cursor do Qt: `xcb-util-cursor` no
Arch, `libxcb-cursor0` no Ubuntu/Debian.

**Windows:** extraia e abra `HaradaER.exe`. Como o programa não é assinado, o Windows mostra
"O Windows protegeu o computador": clique em **Mais informações** › **Executar assim mesmo**.

**macOS:** extraia e mova `HaradaER.app` para Aplicativos. Na primeira vez, o macOS avisa que
não pode verificar o desenvolvedor: clique com o botão direito no app › **Abrir** › **Abrir**
(ou em Ajustes do Sistema › Privacidade e Segurança › **Abrir Mesmo Assim**).

O primeiro início pode levar alguns segundos.

## Observações

- O HaradaER foi desenvolvido e testado no Linux. No Windows e no macOS os testes automáticos
  passam, mas o uso real ainda está começando: avise se algo estranho acontecer.
- Os avisos de licença das bibliotecas incluídas estão em `AVISOS-DE-LICENCA.txt`.
