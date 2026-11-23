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
fazer se não abrir. O `GETTING-STARTED.txt` e o `PRIMEROS-PASOS.txt` são o mesmo manual em
inglês e em espanhol. Depois de aberto, o manual completo está em **Ajuda › Manual do HaradaER**
(F1).

## Observações

- O HaradaER foi desenvolvido e testado no Linux. No Windows e no macOS os testes automáticos
  passam, mas o uso real ainda está começando: avise se algo estranho acontecer.
- O pacote do macOS é gerado e testado no macOS 15. Ele deve abrir no macOS 14, mas isso não é
  mais conferido automaticamente.
- **Novo na 1.6.0 — cópia de recuperação:** enquanto há alterações não salvas, o programa guarda
  uma cópia a cada minuto, fora do seu arquivo. Se ele fechar de repente, na próxima vez que
  abrir oferece recuperar as alterações. O intervalo fica em
  **Configurações › Preferências › Cópia de recuperação**.
- **Espanhol:** a interface inteira e o manual em espanhol. O idioma se troca em
  **Configurações › Preferências** (ou **Ajuda › Trocar o idioma…**) e vale ao reabrir.
- **Menus novos**, iguais nos três sistemas: Arquivo, Editar, Organizar, Exibir,
  **Configurações** (tema, barras, verificação, Edição rápida e Preferências) e Ajuda. O botão
  direito no desenho traz copiar, colar, duplicar, excluir, ordem, agrupar e alinhar.
- **Manual dentro do programa:** **Ajuda › Manual do HaradaER** (F1) abre o manual numa janela,
  sem internet, com busca.
- **Barra de status:** o zoom se digita, e a contagem de erros e avisos abre o painel Mensagens
  com um clique.
- **Atalhos novos, iguais nos três sistemas** (no Mac, Ctrl é Cmd e Alt é Option), para não
  colidir com os atalhos padrão do Mac e do KDE: Agrupar **Ctrl+Alt+G**, Desagrupar
  **Ctrl+Alt+Shift+G**, Trazer para a frente **Home** e Enviar para trás **End** (ou
  Ctrl+Alt+Shift+F e Ctrl+Alt+Shift+B), Selecionar do mesmo tipo **Ctrl+Alt+A** e o novo
  **Desmarcar tudo**, Ctrl+Shift+A.
- **Ctrl+D** volta a duplicar no Linux, onde antes não fazia nada.
- Pequenos ajustes: letras de acesso (Alt+letra) sem repetição nos menus, **Esc** limpa os
  campos de busca, e as caixas de mensagem voltam com os desenhos do sistema (os botões ficam
  só com texto).
- Para relatar um problema ou sugerir uma melhoria: **Ajuda › Relatar um problema** ou
  **Ajuda › Sugerir uma melhoria**, no próprio programa.
- Uma vez por dia, ao abrir, o programa avisa se há versão nova (desliga em
  **Configurações › Preferências › Verificar ao abrir**). **Atualizar e reiniciar** instala a
  versão nova pelo próprio programa, sem precisar baixar à mão.
- Os avisos de licença das bibliotecas incluídas estão em `AVISOS-DE-LICENCA.txt`.

---

## English

Entity-Relationship modeling tool compatible with TerraER 3.14's `.xml` file. The interface is
available in Portuguese, English and Spanish (**Settings › Preferences**; the first time, it
follows the system's language).

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
system: the full step-by-step guide, with what to do if it doesn't open. Once it's open, the full
manual is in **Help › HaradaER Handbook** (F1).

- HaradaER was developed and tested on Linux. On Windows and macOS the automated tests pass,
  but real use is just starting: let us know if anything odd happens.
- The macOS package is built and tested on macOS 15. It should open on macOS 14, but that is no
  longer checked automatically.
- **New in 1.6.0 — recovery copy:** while there are unsaved changes, the program keeps a copy
  every minute, outside your file. If it closes unexpectedly, the next time it opens it offers
  to recover the changes. The interval is in **Settings › Preferences › Recovery copy**.
- **Spanish:** the whole interface and the manual in Spanish. Change the language in
  **Settings › Preferences** (or **Help › Switch application language…**); it applies on reopening.
- **New menus**, the same on the three systems: File, Edit, Arrange, View, **Settings** (theme,
  bars, checking, Quick editing and Preferences) and Help. Right-clicking the drawing gives copy,
  paste, duplicate, delete, order, group and align.
- **Manual inside the program:** **Help › HaradaER Handbook** (F1) opens the manual in a window,
  offline, with search.
- **Status bar:** you can type the zoom, and clicking the error and warning count opens the
  Messages panel.
- **New shortcuts, the same on the three systems** (on a Mac, Ctrl is Cmd and Alt is Option),
  so they don't clash with the standard Mac and KDE shortcuts: Group **Ctrl+Alt+G**, Ungroup
  **Ctrl+Alt+Shift+G**, Bring to front **Home** and Send to back **End** (or Ctrl+Alt+Shift+F
  and Ctrl+Alt+Shift+B), Select same kind **Ctrl+Alt+A** and the new **Deselect all**,
  Ctrl+Shift+A.
- **Ctrl+D** duplicates again on Linux, where it did nothing before.
- Small fixes: menu access keys (Alt+letter) without repeats, **Esc** clears the search fields,
  and message boxes have the system's pictures again (buttons stay text only).
- To report a problem or suggest an improvement: **Help › Report a problem** or
  **Help › Suggest an improvement**, inside the program.
- Once a day, when opening, the program tells you if there's a new version (turn it off in
  **Settings › Preferences › Check when opening**). **Update and restart** installs the new
  version from the program itself, with no manual download.
- The license notices of the bundled libraries are in `AVISOS-DE-LICENCA.txt`.
