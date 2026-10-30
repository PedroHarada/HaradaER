# Primeiros passos

Como baixar, abrir e instalar o HaradaER em cada sistema. Este manual só traz o que já funciona
em cada versão; ele é atualizado conforme o programa for testado em mais lugares. A versão em
inglês é o [Getting started](GETTING-STARTED.md).

Os arquivos ficam na página **Releases** do repositório, na versão mais recente. Não é preciso
instalar Python nem nada mais.

| Sistema | Arquivo | Requisitos |
|---|---|---|
| [Linux](#linux) | `HaradaER-…-linux.tar.gz` | 64 bits, distribuições de 2021 para cá (Ubuntu 22.04+, Arch, Fedora 35+, Mint 21+) |
| [Windows](#windows) | `HaradaER-…-windows.zip` | Windows 10 ou 11, 64 bits |
| [macOS](#macos) | `HaradaER-…-macos.zip` | macOS 14 (Sonoma) ou mais novo, chip Apple (M1 em diante) |

---

## Linux

> **Situação:** testado no uso real (Arch Linux, Wayland).

### Instalar (recomendado)

1. Baixe o `HaradaER-…-linux.tar.gz` e extraia-o numa pasta.
2. Abra um terminal nessa pasta e rode, uma vez só:

   ```
   ./instalar.sh
   ```

3. Procure **HaradaER** no menu de aplicativos. Ele aparece com ícone próprio, e os arquivos
   `.xml` passam a ter a opção **Abrir com › HaradaER**.

Não precisa de `sudo`: o programa vai para `~/.local/bin`, só para o seu usuário. Depois de
instalar, a pasta extraída pode ser apagada. Para atualizar, extraia a versão nova e rode
`./instalar.sh` de novo.

**Desinstalar:** na pasta extraída, `./instalar.sh --remover`. As preferências ficam em
`~/.config/HaradaER` (apague essa pasta se quiser zerá-las).

### Abrir sem instalar

Na pasta extraída, pelo terminal:

```
./HaradaER                  # modelo novo
./HaradaER modelo.xml       # abrir um modelo do TerraER ou do HaradaER
```

O duplo clique no arquivo `HaradaER` costuma **não** funcionar: o gerenciador de arquivos o abre
com outro programa (o navegador, por exemplo). Use o terminal ou o `instalar.sh`.

### Se não abrir

- **Sem Wayland (X11):** instale a biblioteca do cursor do Qt: `xcb-util-cursor` no Arch,
  `libxcb-cursor0` no Ubuntu e no Debian.
- **"Permissão negada":** rode `chmod +x HaradaER instalar.sh` na pasta extraída.

---

## Windows

> **Situação:** o executável é gerado e testado automaticamente a cada versão; o uso real no
> Windows está começando. Avise se algo estranho acontecer.

### Abrir

1. Baixe o `HaradaER-…-windows.zip`.
2. Clique com o botão direito no arquivo › **Extrair tudo…** › **Extrair**.
3. Abra o `HaradaER.exe` da pasta extraída.
4. Na primeira vez, o Windows mostra **"O Windows protegeu o computador"**, porque o programa
   não tem assinatura digital. Clique em **Mais informações** (o link embaixo do texto) e depois
   em **Executar assim mesmo**. Nas próximas vezes, o aviso não aparece.

Não há instalação: o `HaradaER.exe` roda de onde estiver. Para ter um atalho, clique com o botão
direito nele › **Enviar para** › **Área de trabalho (criar atalho)** (no Windows 11, o
**Enviar para** fica em **Mostrar mais opções**).

Para atualizar, baixe a versão nova e substitua o `HaradaER.exe` antigo.

### Se não abrir

- **Não aparece "Executar assim mesmo":** clique com o botão direito no `HaradaER.exe` ›
  **Propriedades**, marque **Desbloquear** embaixo, na aba Geral, › **OK**, e abra de novo.
  Em computadores de escola ou de empresa, a política da máquina pode impedir; nesse caso, só
  o administrador pode liberar.
- **Demora para abrir:** o primeiro início leva alguns segundos (o programa se descompacta numa
  pasta temporária). Espere antes de clicar de novo.

---

## macOS

> **Situação:** o aplicativo é gerado e testado automaticamente a cada versão, mas ainda não foi
> aberto num Mac de verdade. Os passos abaixo são os do macOS para qualquer aplicativo sem
> assinatura; avise como foi.

### Instalar

1. Baixe o `HaradaER-…-macos.zip` e abra-o (o Finder extrai sozinho).
2. Arraste o **HaradaER.app** para a pasta **Aplicativos**.
3. Na primeira vez, o macOS avisa que não pode verificar o desenvolvedor, porque o aplicativo não
   tem assinatura da Apple:
   - clique com o botão direito (ou Control + clique) no HaradaER › **Abrir** › **Abrir**; ou
   - se não houver o botão **Abrir** (macOS 15 em diante), vá em **Ajustes do Sistema ›
     Privacidade e Segurança**, role até o aviso sobre o HaradaER e clique em
     **Abrir Mesmo Assim**.

   Nas próximas vezes, ele abre normalmente pelo Launchpad ou pelo Dock.

Para atualizar, arraste a versão nova para Aplicativos e escolha **Substituir**.

---

## Depois de abrir

O uso é o mesmo em qualquer sistema. O HaradaER abre no idioma do sistema (português ou inglês);
para trocar, use **Exibir › Idioma** e abra o programa de novo. Para começar:

1. Escolha **Entidade** na faixa de cima e clique no desenho; digite o nome e Enter.
2. Crie um **Relacionamento** e outra entidade do mesmo jeito.
3. Selecione o relacionamento e uma entidade (Ctrl + clique; no Mac, Cmd + clique): as conexões
   que servem para o par ficam destacadas em azul na faixa. Clique numa delas para ligar os dois.
4. **Arquivo › Salvar** grava um `.xml` que também abre no TerraER 3.14.

Contornos laranja e o painel **Mensagens** apontam o que falta no modelo, como uma entidade sem
atributo chave. Dá para desligá-los em **Exibir › Avisos de estrutura**.

O HaradaER não usa a conexão livre do TerraER, que não tem significado no modelo. Se um
arquivo tiver alguma, ela é apagada ao abrir, com um aviso dizendo entre quais elementos estava;
o arquivo só muda quando você salvar.

Achou um problema ou tem uma ideia? **Ajuda › Relatar um problema** e **Ajuda › Sugerir uma
melhoria** abrem a página do GitHub já preenchida (é preciso uma conta no GitHub).

Uma vez por dia, ao abrir, o HaradaER confere no GitHub se há versão nova e avisa; nada é
baixado sozinho. Para desligar, desmarque **Ajuda › Verificar ao abrir**.

Todos os comandos estão em [Como usar](../README.md#como-usar), no README.

---

## Atalhos do teclado

A mesma lista está em **Ajuda › Atalhos do teclado** (F1), com busca. Os atalhos de uma tecla
valem com **Editar › Edição rápida** ligada (Ctrl+Shift+E, ou o botão na barra de status).
Com Selecionar ativo e um elemento selecionado, a letra da família dele troca o tipo (por
exemplo, A num atributo o faz virar chave).

<!-- atalhos: início (gerado por python -m haradaer.gui.shortcuts_dialog) -->

**Arquivo**

| Ação | Atalho |
|---|---|
| Novo | `Ctrl+N` |
| Abrir | `Ctrl+O` |
| Salvar | `Ctrl+S` |
| Salvar como | `Ctrl+Shift+S` |
| Exportar desenho | `Ctrl+E` |
| Fechar | `Ctrl+F4` |

**Editar**

| Ação | Atalho |
|---|---|
| Desfazer | `Ctrl+Z` |
| Refazer | `Ctrl+Y` |
| Recortar | `Ctrl+X` |
| Copiar | `Ctrl+C` |
| Colar | `Ctrl+V` |
| Duplicar | `Ctrl+D` |
| Excluir | `Del` |
| Selecionar tudo | `Ctrl+A` |
| Selecionar do mesmo tipo | `Ctrl+Shift+A` |
| Localizar | `Ctrl+F` |
| Copiar como imagem | `Ctrl+Shift+C` |
| Edição rápida | `Ctrl+Shift+E` |

**Organizar**

| Ação | Atalho |
|---|---|
| Trazer para a frente | `Ctrl+]` |
| Enviar para trás | `Ctrl+[` |
| Agrupar | `Ctrl+G` |
| Desagrupar | `Ctrl+Shift+G` |

**Exibir**

| Ação | Atalho |
|---|---|
| Ampliar | `Ctrl++` |
| Reduzir | `Ctrl+-` |
| Tamanho real | `Ctrl+0` |
| Ajustar à janela | `Ctrl+9` |
| Grade | `Ctrl+'` |

**Ajuda**

| Ação | Atalho |
|---|---|
| Atalhos do teclado | `F1` |

**Edição rápida (Editar › Edição rápida)**

| Ação | Atalho |
|---|---|
| Selecionar | `V` |
| Entidade → Entidade fraca → Entidade associativa | `E` |
| Relacionamento → Relacionamento fraco | `R` |
| Atributo → Atributo chave → Atributo chave parcial → Atributo multivalorado → Atributo derivado | `A` |
| Disjunção → Sobreposição → União | `G` |
| Participação, lado "1" → Participação total, lado "1" | `1` |
| Participação, lado "N" → Participação total, lado "N" | `N` |
| Ligação de atributo | `L` |
| Generalização simples → Participação opcional em generalização → Participação obrigatória em generalização | `H` |
| Voltar uma posição no ciclo | `Shift + letra` |
| Trocar o tipo do elemento selecionado (com Selecionar) | `Letra da família` |
| Criar onde está o mouse | `Espaço` |
| Voltar para Selecionar | `Esc` |

**Mouse e gestos**

| Ação | Atalho |
|---|---|
| Zoom | `Pinça` `ou Ctrl + roda do mouse` |
| Rolar o desenho | `Dois dedos` `ou a roda do mouse` |
| Mover o desenho | `Botão do meio e arrastar` |
| Manter a ferramenta depois de criar | `Shift + clique` |
| Editar o nome | `Duplo clique no elemento` |
| Novo vértice na conexão | `Duplo clique na linha` |
| Tirar um vértice | `Duplo clique no vértice` |

<!-- atalhos: fim -->
