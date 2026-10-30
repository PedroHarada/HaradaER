Ferramenta de modelagem Entidade-Relacionamento compatível com o arquivo `.xml` do TerraER 3.14.

## Baixar

| Sistema | Arquivo | Requisitos |
|---|---|---|
| Linux | `HaradaER-…-linux.tar.gz` | Distribuições de 2021 para cá (Ubuntu 22.04+, Arch, Fedora 35+, Mint 21+), 64 bits |
| Windows | `HaradaER-…-windows.zip` | Windows 10 ou 11, 64 bits |
| macOS | `HaradaER-…-macos.zip` | macOS 14 (Sonoma) ou mais novo, chip Apple (M1 em diante) |

Não precisa instalar Python nem nada mais: é só extrair e abrir.

## Como abrir

**Linux:** extraia e, na pasta extraída, rode `./instalar.sh` uma vez. O HaradaER aparece no
menu de aplicativos, com ícone, e os arquivos `.xml` passam a ter a opção "Abrir com HaradaER".
Não precisa de sudo, e `./instalar.sh --remover` desinstala. Sem instalar, dá para abrir pelo
terminal com `./HaradaER` (o duplo clique no arquivo costuma abrir outro programa). Em X11 (sem Wayland), se não abrir, instale a biblioteca do cursor do Qt: `xcb-util-cursor` no
Arch, `libxcb-cursor0` no Ubuntu/Debian.

**Windows:** extraia e abra `HaradaER.exe`. Como o programa não é assinado, o Windows mostra
"O Windows protegeu o computador": clique em **Mais informações** › **Executar assim mesmo**.

**macOS:** extraia e mova `HaradaER.app` para Aplicativos. Na primeira vez, o macOS avisa que
não pode verificar o desenvolvedor: clique com o botão direito no app › **Abrir** › **Abrir**
(ou em Ajustes do Sistema › Privacidade e Segurança › **Abrir Mesmo Assim**).

O primeiro início pode levar alguns segundos.

Cada pacote traz o `PRIMEIROS-PASSOS.txt` do seu sistema: o passo a passo completo, com o que
fazer se não abrir. O `GETTING-STARTED.txt` é o mesmo manual em inglês.

## Observações

- O HaradaER foi desenvolvido e testado no Linux. No Windows e no macOS os testes automáticos
  passam, mas o uso real ainda está começando: avise se algo estranho acontecer.
- A conexão livre não existe mais: ao abrir um arquivo que tenha alguma, ela é apagada, com um
  aviso dizendo entre quais elementos estava. O arquivo só muda quando você salvar.
- Para relatar um problema ou sugerir uma melhoria: **Ajuda › Relatar um problema** ou
  **Ajuda › Sugerir uma melhoria**, no próprio programa.
- Uma vez por dia, ao abrir, o programa avisa se há versão nova (desliga em
  **Ajuda › Verificar ao abrir**). Nada é baixado sozinho.
- Os avisos de licença das bibliotecas incluídas estão em `AVISOS-DE-LICENCA.txt`.

---

## English

Entity-Relationship modeling tool compatible with TerraER 3.14's `.xml` file. The interface is
available in Portuguese and English (**View › Language**; the first time, it follows the
system's language).

| System | File | Requirements |
|---|---|---|
| Linux | `HaradaER-…-linux.tar.gz` | Distributions from 2021 on (Ubuntu 22.04+, Arch, Fedora 35+, Mint 21+), 64-bit |
| Windows | `HaradaER-…-windows.zip` | Windows 10 or 11, 64-bit |
| macOS | `HaradaER-…-macos.zip` | macOS 14 (Sonoma) or newer, Apple chip (M1 onward) |

No need to install Python or anything else: just extract and open.

**Linux:** extract it and, in the extracted folder, run `./instalar.sh` once. HaradaER shows up
in the applications menu, with its icon, and `.xml` files get the option "Open with HaradaER".
No sudo needed, and `./instalar.sh --remover` uninstalls it. Without installing, open it from
the terminal with `./HaradaER` (double-clicking the file usually opens another program). On X11
(without Wayland), if it doesn't open, install Qt's cursor library: `xcb-util-cursor` on Arch,
`libxcb-cursor0` on Ubuntu/Debian.

**Windows:** extract it and open `HaradaER.exe`. Since the program isn't signed, Windows shows
"Windows protected your PC": click **More info** › **Run anyway**.

**macOS:** extract it and move `HaradaER.app` to Applications. The first time, macOS warns that
it can't verify the developer: right-click the app › **Open** › **Open** (or System Settings ›
Privacy & Security › **Open Anyway**).

The first start may take a few seconds. Each package includes `GETTING-STARTED.txt` for its
system: the full step-by-step guide, with what to do if it doesn't open.

- HaradaER was developed and tested on Linux. On Windows and macOS the automated tests pass,
  but real use is just starting: let us know if anything odd happens.
- The free connection no longer exists: when a file has any, they are deleted on opening, with a
  notice saying which elements they connected. The file only changes when you save.
- To report a problem or suggest an improvement: **Help › Report a problem** or
  **Help › Suggest an improvement**, inside the program.
- Once a day, when opening, the program tells you if there's a new version (turn it off in
  **Help › Check when opening**). Nothing is downloaded by itself.
- The license notices of the bundled libraries are in `AVISOS-DE-LICENCA.txt`.
