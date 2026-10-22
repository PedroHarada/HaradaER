# HaradaER — Documento de Requisitos

Versão 1.0 · 2026-10-20 · Revisão da v1

Convenção: salvo indicação em contrário, todo requisito é **obrigatório** para a v1.

## 1. Visão geral

O **HaradaER** é uma ferramenta acadêmica de modelagem Entidade-Relacionamento (ER), escrita em Python, cujo comportamento e notação seguem integralmente o **TerraER 3.14** (R. Terra e H. Rocha).

O TerraER é tomado como **especificação de referência**: em caso de dúvida, vale o que o TerraER faz.

### 1.1 Requisito central: compatibilidade de arquivo

> **RNF-01** — Todo modelo salvo pelo HaradaER deve poder ser aberto no TerraER 3.14 e exibir **o mesmo modelo, sem erro e sem perda**. O inverso também vale: todo `.xml` salvo pelo TerraER 3.14 deve ser aberto pelo HaradaER.

Cenário de aceitação: o usuário salva um `.xml` no HaradaER e o envia a um colega; o colega abre o arquivo no TerraER e vê os mesmos elementos, posições, rótulos, tipos e conexões.

### 1.2 Fonte das informações

Tudo neste documento foi levantado a partir do `TerraER3.14.jar` (somente consulta, ignorado pelo git):

- `javap` sobre as classes, para obter tags, atributos e regras.
- Execução **headless** das próprias classes do TerraER (`harness/`) para gerar `.xml` reais e testar a validação de conexões.
- Teste prático de gestos de trackpad com PySide6 6.12.0 (Qt 6.12.0) em Linux/Wayland (seção 6.1, RF-15).

Os arquivos em `docs/referencia-terraer/` são a saída real do TerraER e servem de **golden files** (seção 7).

**Limitação.** A leitura e a escrita foram verificadas com as classes de leitura/escrita do TerraER (`DOMStorableInputOutputFormat`), não com a interface gráfica. A abertura pela GUI continua sendo um critério de aceitação manual (seção 7).

## 2. Escopo

**Dentro do escopo (v1):**
- Criar, editar, salvar e abrir modelos ER no formato do TerraER.
- Toda a notação ER do TerraER (seção 3).
- Verificação do modelo (validação de conexões).
- Exportação para imagem.
- Interface Qt com painéis acopláveis e gestos de trackpad (RNF-09, RF-15).

**Fora do escopo (v1):**
- Banco de dados real, engenharia reversa a partir de SQL, edição colaborativa.
- Qualquer extensão do formato que o TerraER não leia (ver RNF-02).
- Interface de linha de comando (RNF-08).
- Compatibilidade da área de transferência com a do TerraER (copiar e colar de elementos entre os dois programas): **descartada** (QA-13).
- Exportação para GIF: **descartada** (QA-14).
- Geração de DDL SQL (RF-13): adiada para depois da v1; o levantamento do TerraER já está feito (`INVESTIGACOES.md` seção 6).
- Edição da instrução SQL do atributo derivado e Modo de Edição Rápida (RF-20): adiados. A instrução SQL já gravada num arquivo continua sendo lida e regravada.
- Impressão (RF-14): **descartada**; o PDF de Exportar desenho cobre a necessidade.

## 3. Elementos do modelo

Tag XML = nome usado no arquivo. Nomes entre parênteses são as classes originais do TerraER.

### 3.1 Elementos (nós)

| Elemento | Tag | Observação |
|---|---|---|
| Entidade | `ent` | Retângulo. |
| Entidade fraca | `entfraca` | Retângulo de borda dupla. |
| Relacionamento | `rel` | Losango. |
| Relacionamento fraco (identificador) | `relfraco` | Losango de borda dupla. |
| Entidade associativa (entidade-relacionamento) | `entrel` | Retângulo com losango. |
| Atributo | `atr` | Elipse. Tem tipo e anulabilidade. |
| Atributo chave | `atrchave` | Texto em negrito e sublinhado. Tem tipo e anulabilidade. |
| Atributo chave parcial | `atrchaveparcial` | Elipse com texto em negrito e **tracejado** (o tracejado é do texto). Tem tipo e anulabilidade. |
| Atributo derivado | `atrderivado` | Elipse tracejada. **Sem** tipo nem anulabilidade. Tem a instrução SQL opcional, gravada no atributo `sql` (ver `INVESTIGACOES.md` seção 8). |
| Atributo multivalorado | `atrmulti` | Elipse de borda dupla. Tem tipo e anulabilidade. |
| Generalização: união | `uniao` | Círculo com "u". |
| Generalização: disjunção | `disjuncao` | Círculo com "d". |
| Generalização: sobreposição | `sobreposicao` | Círculo com "o". |

Também existem no formato, como figuras de apoio: texto (`t`, `tn` negrito, `ti` itálico, `ta` área de texto), retângulo (`r`), elipse (`e`), losango (`diamond`), círculo (`circ`), linha (`l`), bézier (`b`/`bezier`), imagem (`image`) e grupo (`g`). O HaradaER deve ao menos **ler e preservar** essas figuras (RF-12).

### 3.2 Conexões

| Conexão | Tag | Uso |
|---|---|---|
| Conexão livre | `llabel` | Sem restrição de validação. |
| Participação, lado "1" | `llabelUm` | Mostra o rótulo `1`. |
| Participação, lado "N" | `llabelMuitos` | Mostra o rótulo `N`. |
| Participação total, lado "1" | `llabelDoubleUm` | Linha dupla, rótulo `1`. |
| Participação total, lado "N" | `llabelDoubleMuitos` | Linha dupla, rótulo `N`. |
| Ligação de atributo | `lcaf` (também `lcf`) | Atributo ↔ entidade/relacionamento/atributo. |
| Generalização simples | `generalizacaoLine` | Sem rótulo. Entidade ↔ generalização. |
| Participação **opcional** em disjunção/sobreposição | `llabelGeneralizacao` | Rótulo editável, gravado no atributo `labelGeneralizacaoText`. |
| Participação **obrigatória** em disjunção/sobreposição | `llabelDoubleGeneralizacao` | Linha dupla, também com `labelGeneralizacaoText`. |

O rótulo `1` é implícito na tag. Nas conexões "N", o TerraER numera as de um mesmo relacionamento como N, M, P, Q, R, S e grava a letra no estilo da conexão (`<a><text><string>M</string></text></a>`); sem esse bloco, vale `N` (`INVESTIGACOES.md`, seção 15).

### 3.3 Tipos de atributo

Gravados no atributo XML `attributeType` com o **tipo SQL**, não com o nome do tipo:

| Tipo no TerraER | Valor gravado | Observação |
|---|---|---|
| CHAR | `CHAR(128)` | |
| TEXT | `VARCHAR2(128)` | |
| INTEGER | `NUMBER` | Mesmo valor gravado de NUMBER. |
| NUMBER | `NUMBER(9,2)` | |
| DATE | `DATE` | |

> **Atenção.** No enum do TerraER, `INTEGER` tem tipo SQL `NUMBER` e `NUMBER` tem `NUMBER(9,2)`. Um atributo chave novo (tipo padrão INTEGER) foi gravado como `attributeType="NUMBER"` nas amostras. O HaradaER deve gravar exatamente esses valores, sem "corrigi-los" (RNF-03). Ao reler, o TerraER interpreta `NUMBER` como INTEGER e `NUMBER(9,2)` como NUMBER. Um valor fora dos cinco acima é lido **sem erro**, mas o TerraER falha ao salvar o arquivo (`INVESTIGACOES.md` seção 1); por isso o HaradaER nunca deve gravar outro valor.

`nullable` é `true` ou `false`.

## 4. Formato do arquivo (resumo normativo)

Detalhes completos nas amostras de `docs/referencia-terraer/`.

### 4.1 Estrutura

- **Sem** declaração `<?xml ...?>` e **sem** DOCTYPE. O arquivo gravado é **ASCII puro**: `& < > " '` viram `&amp; &lt; &gt; &quot; &apos;`, `\n` fica literal, e todo outro caractere abaixo de 0x20 ou a partir de 0x7f vira referência hexadecimal minúscula (`ç` → `&#xe7;`, tabulação → `&#x9;`). Caracteres acima de U+FFFF (emojis) são gravados como **dois** pedaços (`😀` → `&#xd83d;&#xde00;`); o TerraER corrompe `&#x1f600;`. O TerraER também grava caracteres de controle como `&#x1;`, que XML puro proíbe: o HaradaER recusa esse arquivo com erro claro. Na leitura, aceitar também UTF-8 direto.
- Quebras de linha dentro de textos são gravadas como `\n` literal, sem escape. Em **atributos**, um `\n` literal é normalizado para espaço pelo parser XML padrão; só afeta rótulos de generalização com quebra de linha, e fica como limitação conhecida.
- Elemento sem conteúdo é gravado como `<tag/>` (inclusive texto vazio: `<string/>`); atributo vazio fica `sql=""`; valor nulo não é gravado.
- Números: inteiros sem casa decimal (`100`, `-0`); decimais como `Double.toString` do Java sem o `.0` final (`16.344114303588867`), em notação científica fora de 10⁻³ ≤ |x| < 10⁷ (`1.0E-5`, `1.0E7`, `1.0E10`). O Java mostra ao menos dois dígitos (`4.9E-324`).
- Uma única linha, **sem indentação**.
- Raiz `<drawing>` → filho `<figures>` → uma figura por filho, na ordem de empilhamento (z-order).
- Extensão `.xml`.

### 4.2 Identificadores e referências

- Todo objeto recebe `id="<hex>"`, sequencial em ordem de escrita, a partir de `0`, em hexadecimal minúsculo (`0`…`f`, `10`, `1a`…).
- Uma referência a objeto já escrito usa `<tag ref="<id>"/>`. Exemplo: `<Owner><ent ref="0"/></Owner>`.
- **Ordem de empilhamento:** se uma conexão vem antes do nó na lista de figuras, o nó é escrito por inteiro **dentro** do `Owner` da conexão, e depois aparece no desenho só como `<ent ref="2"/>`. Os ids seguem a ordem em que cada objeto aparece pela primeira vez. Ver `referencia-terraer/amostra-ordem-empilhamento.xml`.

### 4.3 Elementos compostos

Entidade, relacionamento e demais nós são **grupos**: contêm `<children>` com as formas internas e o texto.

```xml
<ent id="0"><children>
  <r id="1" x="50" y="50" w="100" h="40"/>
  <t id="2" x="83.57" y="61.82"><a><text><string>Aluno</string></text></a></t>
</children></ent>
```

- O nome do elemento é o texto de `<t>` (ou `<tn>`).
- Estilo vai em `<a>` (atributos de aparência): `strokeType` (enum `DOUBLE`), `innerStrokeWidthFactor` (`3`), `strokeDashes` (lista de doubles), `fillColor` (`<color rgba="#aarrggbb"/>`), `fontBold`, `fontUnderlined`, `fontSize`, `text`.
- `x`, `y`, `w`, `h` são números decimais (inteiros sem `.0`).
- Atributos de tipo ficam no próprio elemento: `<atr id=".." nullable="true" attributeType="CHAR(128)">`.
- O atributo derivado guarda a instrução SQL: `<atrderivado id=".." sql="SELECT ...">`.

### 4.4 Conexões

```xml
<llabelUm id="f">
  <points>
    <p colinear="true" x="150" y="64.15" c1x="0" c1y="0" c2x="0" c2y="0"/>
    <p colinear="true" x="230" y="54.80" c1x="0" c1y="0" c2x="0" c2y="0"/>
  </points>
  <startConnector><rConnector id="10"><Owner><ent ref="0"/></Owner></rConnector></startConnector>
  <endConnector><rConnector id="11"><Owner><rel ref="6"/></Owner></rConnector></endConnector>
</llabelUm>
```

- A conexão referencia os dois nós por `Owner` + `ref`.
- Ponta ainda não ligada: `<startConnector><null/></startConnector>` (ou `endConnector`). O elemento `<null/>` é válido onde se espera um objeto.
- O conector é `rConnector` nas amostras (retangular). Existem também `ellipseConnector`, `diamondConnector` e `bezierConnector`; devem ser lidos.

### 4.5 Tolerâncias observadas

- A **ordem** dos filhos dentro de `<a>` não é significativa: o TerraER relê e regrava em outra ordem (teste de ida e volta).
- Leitura no TerraER (`INVESTIGACOES.md` seção 2): tag desconhecida **impede abrir o arquivo**; atributo ou chave de estilo desconhecidos são ignorados; declaração XML, indentação, DOCTYPE e UTF-8 direto são aceitos; `id` repetido ou `ref` inexistente fazem falhar.
- Textos padrão de novos elementos mudam com o idioma (inglês em headless: `rel. 0`, `W. ENT. 0`, `key att. 0`; o jar tem `Labels_pt`). O texto gravado é o do usuário, então o idioma não afeta a compatibilidade.

### 4.6 Aparência (como o TerraER desenha)

Para o diagrama ficar igual ao do TerraER (detalhes e evidências em `INVESTIGACOES.md` seção 13):

- O preenchimento do retângulo, do losango e da elipse é **fixo por tipo de forma** e ignora o `fillColor` do arquivo: verde `(175,255,175)`, amarelo `(255,255,100)` e lilás `(175,175,255)`. Só o círculo usa o `fillColor`.
- Traço duplo: duas faixas de largura `w` com vão de `w × (fator − 1)`.
- Rótulos `1`, `N` e o texto da generalização seguem a regra de posição do TerraER (8 unidades, −45°).
- A conexão `generalizacaoLine` leva um arco de 210° no centro.

## 5. Regras de validação de conexões

O TerraER **não impede** conexões inválidas: ele só as pinta de **vermelho** ("Verificação do Modelo", ligável/desligável). A validade abaixo foi medida executando `ModelValidation` do TerraER (`harness/Matrix.java`).

Legenda: **E** = ent, **EF** = entfraca, **R** = rel, **RF** = relfraco, **ER** = entrel, **A\*** = qualquer atributo, **G\*** = uniao/disjuncao/sobreposicao.

| Conexão | Pares válidos (origem → destino) |
|---|---|
| `llabel` | Qualquer nó para qualquer nó (sempre válida). |
| `llabelUm`, `llabelMuitos` | `E→R`, `E→RF`, `E→ER`, `EF→R`, `EF→ER`, `R→E`, `R→EF`, `R→ER`, `RF→E`, `RF→ER`, `ER→E`, `ER→EF`, `ER→R`, `ER→RF`. |
| `llabelDoubleUm`, `llabelDoubleMuitos` | Os mesmos de cima **mais** `EF→RF` e `RF→EF`. |
| `lcaf` | Atributo ligado ao dono. Ver tabela abaixo. |
| `generalizacaoLine` | `E→E`, `G*→E`. |
| `llabelGeneralizacao`, `llabelDoubleGeneralizacao` | `E→G*`, `EF→G*`, `ER→G*`, `G*→E`, `G*→EF`, `G*→ER`. |

Dono × atributo em `lcaf` (qualquer direção; o par de ids segue a origem):

| Dono | Atributos aceitos |
|---|---|
| `ent` | `atr`, `atrchave`, `atrderivado`, `atrmulti` |
| `entfraca` | `atr`, `atrchaveparcial`, `atrderivado`, `atrmulti` |
| `rel`, `relfraco` | `atr`, `atrderivado`, `atrmulti` |
| `entrel` | `atr`, `atrchave`, `atrderivado`, `atrmulti` |
| `atr` | `atr` (atributo composto); `atrmulti` (**só no HaradaER**) |
| `atrchave`, `atrchaveparcial` | `atr` (chave composta; **só no HaradaER**) |
| `atrmulti` | `atr`, `atrmulti` (multivalorado composto; **só no HaradaER**) |

> A tabela de `lcaf` vale **nas duas direções**: a validação do TerraER é simétrica (por exemplo, `atr→ent` é tão válido quanto `ent→atr`). Ver QA-03 e `INVESTIGACOES.md` seção 4.

> **Diferença deliberada:** o TerraER só aceita sub-atributo simples em atributo simples. O
> modelo ER aceita mais (Elmasri e Navathe, cap. 3): chave composta (`Registration(State,
> Number)` em CARRO), multivalorado composto (`{PreviousDegrees (College, Year, Degree,
> Field)}`, ou o telefone com DDD e número) e aninhamento em qualquer nível (um composto com
> parte multivalorada). O HaradaER aceita esses pares na verificação; o arquivo não muda e
> continua abrindo no TerraER, que apenas segue marcando a linha. Os pares ficam em
> `BEYOND_TERRAER` (`core/rules/tables.py`), e os testes conferem que o resto é igual ao TerraER.
> Continuam inválidos: chave dentro de chave, chave multivalorada e derivado com partes.

**Avisos de estrutura** (`core/rules/structure.py`; Exibir › Avisos de estrutura, ligados por
padrão e lembrados entre sessões). Contorno laranja tracejado no elemento, com a explicação na
dica. Olham o modelo inteiro e só apontam o que a teoria considera errado em qualquer caso:

| Aviso | Exceções (sem aviso) |
|---|---|
| Entidade sem atributo chave | Subclasse de especialização (herda a chave), entidade ligada a uma união (categoria) e entidade associativa (a chave vem do relacionamento) |
| Entidade fraca sem relacionamento identificador | |
| Relacionamento identificador sem entidade fraca | |
| Relacionamento com menos de dois participantes | O recursivo conta duas vezes, uma por papel |
| Especialização (círculo) com menos de dois elementos ligados | |
| Atributo sem ligação de atributo com um dono | |

Sem aviso para entidade fraca sem chave parcial: ela normalmente tem uma, mas pode não ter.

O TerraER também oferece "Recomendar conexão" (`ConnectionRecommendationAction`): dados dois elementos, lista as ligações válidas entre eles (RF-10).

## 6. Requisitos

### 6.1 Requisitos funcionais

| ID | Requisito |
|---|---|
| RF-01 | Criar, abrir, salvar e salvar como modelo `.xml` (RNF-01), com projetos recentes. |
| RF-02 | Inserir todos os elementos da seção 3.1 e todas as conexões da seção 3.2. |
| RF-03 | Mover, redimensionar, copiar, colar, duplicar, excluir, agrupar e desagrupar. |
| RF-04 | Editar o nome dos elementos e o rótulo das generalizações. |
| RF-05 | Escolher tipo e anulabilidade dos atributos (seção 3.3). Atributo derivado não tem tipo. |
| RF-06 | Desfazer e refazer (o TerraER tem `UndoAction`/`RedoAction`). |
| RF-07 | Zoom, grade, alinhamento, trazer para frente e enviar para trás, selecionar todos do mesmo tipo. |
| RF-08 | Localizar elementos no modelo. |
| RF-09 | Verificação do modelo: destacar em vermelho as conexões com problema, com opção de ligar e desligar. Tem problema a conexão (exceto a livre, `llabel`) que tenha uma ponta solta ou que ligue um par de elementos que o tipo não aceita (seção 5). Também avisa, em laranja e com opção de desligar, os problemas de estrutura da seção 5. |
| RF-10 | Recomendação de conexão entre dois elementos selecionados (tipos de conexão válidos para o par) e dos elementos possíveis para um tipo de conexão. Usa a mesma tabela da verificação, então nunca recomenda algo que apareceria em vermelho; difere do TerraER em dois pontos (`INVESTIGACOES.md` seção 12). A conexão livre não é recomendada. |
| RF-11 | Exportar para imagem (PNG e JPG), para SVG e para PDF, e copiar o modelo como imagem para a área de transferência. GIF fica fora: o Qt não grava GIF. |
| RF-12 | Preservar sem alteração as figuras de apoio **conhecidas** lidas de um arquivo (texto livre, formas, imagem, grupo) e seus atributos de estilo, regravando-as iguais. Tags desconhecidas não existem em arquivos válidos do TerraER e geram erro (RNF-14). |
| RF-13 | **(Fora da v1)** Gerar o DDL SQL do modelo. Regras e defeitos do TerraER levantados em `INVESTIGACOES.md` seção 6. Quando voltar ao escopo, decidir entre reproduzir o TerraER e gerar SQL válido com as mesmas convenções. |
| RF-14 | **(Descartado, decisão do autor em 2026-10-22)** Imprimir. O PDF de Exportar desenho cobre a necessidade. |
| **RF-15** | **Gestos de trackpad (obrigatório).** Na área do diagrama: pinça com dois dedos para zoom e rolagem com dois dedos para mover a visão. O zoom e a rolagem por teclado e menu continuam disponíveis como alternativa. Teste em Linux/Wayland com PySide6 6.12.0 confirmou: o zoom chega como `QNativeGestureEvent` do tipo `ZoomNativeGesture` (591 eventos, valores de -0,043 a +0,059 por evento, que se acumulam na escala) e a rolagem como `QWheelEvent` com `pixelDelta` e fases `ScrollBegin`/`ScrollUpdate` (145 eventos). A API `QPinchGesture` **não** disparou no Wayland; usar o evento nativo. Na v1 os gestos são considerados só no Linux/Wayland desta máquina, onde foram verificados; nos demais sistemas valem apenas as alternativas de teclado e menu (QA-11). |
| RF-16 | Inspetor de objetos: painel com a lista/árvore dos elementos do modelo, que permite selecionar um elemento e localizá-lo no diagrama (o TerraER tem o "Inspetor de Objetos"). |
| RF-17 | Perguntar se deseja salvar as alterações ao fechar um documento modificado ou sair (Salvar / Não salvar / Cancelar), e mostrar mensagem clara quando não for possível gravar o arquivo. |
| RF-18 | Edição do nome diretamente sobre o elemento (campo de texto flutuante), sem abrir diálogo. |
| RF-19 | Uma janela por documento (decisão do autor, igual ao TerraER): cada modelo abre na sua própria janela, com painéis, zoom e histórico de desfazer independentes, e vários modelos podem ficar abertos ao mesmo tempo. Sem abas. |
| RF-20 | **Instrução SQL do atributo derivado:** ler e gravar o atributo `sql` de `atrderivado` sem perdê-lo (RNF-01). **Fora da v1:** editar essa instrução na interface e o Modo de Edição Rápida (`INVESTIGACOES.md` seções 7 e 8). |

### 6.2 Requisitos não funcionais

| ID | Requisito |
|---|---|
| **RNF-01** | **Compatibilidade bidirecional com o `.xml` do TerraER 3.14** (seção 1.1). |
| RNF-02 | O HaradaER **não pode gravar** tags que o TerraER desconheça: o TerraER recusa abrir o arquivo inteiro (verificado). Atributos e chaves de estilo desconhecidos são ignorados na leitura, mas descartados ao salvar de novo, então também não servem para guardar dados do HaradaER. Qualquer dado extra fica em arquivo separado, nunca dentro do `.xml`. |
| RNF-03 | Reproduzir quirks do formato, como `INTEGER` gravado como `NUMBER` (seção 3.3), sem "corrigi-los". |
| RNF-04 | Leitura tolerante: aceitar qualquer ordem de filhos em `<a>`, com ou sem quebras de linha, e ids em qualquer ordem, desde que consistentes. |
| RNF-05 | Escrita conservadora: seguir a seção 4.1 (ASCII com referências numéricas, sem declaração XML, sem DOCTYPE, números no formato Java). |
| RNF-06 | Interface em português, com opção de inglês, como o TerraER (`Labels_pt` / `Labels_en`). A troca de idioma vale ao reabrir o programa, que avisa disso; os nomes padrão dos elementos novos seguem o idioma; o manual também tem versão em inglês (decisões do autor em 2026-10-22). |
| RNF-07 | **Plataforma da v1:** Linux com Wayland, que é onde o HaradaER é desenvolvido e testado, com **Python 3.14** e **PySide6 6.12** (as versões verificadas). Outras versões do Python, Windows, macOS e Linux com X11 não são alvo da v1: o código não deve impedi-los (nada específico de Linux fora de `gui`), mas não são verificados. |
| RNF-08 | Arquitetura em camadas: um **núcleo** (modelo, leitura/escrita do `.xml`, validação e, no futuro, DDL) que não importa nada de interface gráfica, e uma interface gráfica fina por cima. Isso permite testar a compatibilidade (seção 7) sem tela. Uma CLI é opcional e fica fora da v1 salvo decisão contrária. |
| RNF-09 | A interface gráfica usa **Qt**, o mesmo sistema do Octave, via **PySide6** (LGPL; funcionou no teste de gestos, Qt 6.12.0). Organização de janela como a do Octave: painéis acopláveis, redimensionáveis e que podem ser ocultados, em volta da área central do diagrama. Painéis previstos: paleta de elementos, inspetor de objetos (RF-16) e mensagens da verificação do modelo (RF-09). A disposição dos painéis é lembrada entre sessões. Lista de painéis confirmada pelo autor. |
| RNF-10 | **Abertura segura de arquivos recebidos.** O `.xml` pode vir de terceiros. A leitura não pode resolver entidades externas nem DTD, e deve limitar tamanho e profundidade, para evitar ataques de expansão de entidades e leitura de arquivos locais. Um arquivo inválido ou truncado gera mensagem de erro e **não** derruba o programa nem altera o arquivo. |
| RNF-11 | **Gravação segura.** Salvar escreve primeiro num arquivo temporário e só então substitui o original, para que uma falha no meio nunca corrompa um modelo existente. |
| RNF-12 | **Testes automatizados** do núcleo, sem tela: golden files, ida e volta e estrutura (seção 7). A verificação com as classes do TerraER exige um JDK, mas só nos testes, nunca para usar o HaradaER. |
| RNF-14 | **Erros de leitura claros.** Se o arquivo tiver tag desconhecida, raiz diferente de `drawing`, `id` repetido, referência a id inexistente ou XML truncado, o HaradaER **não abre** o arquivo e mostra uma mensagem que diz o problema e, quando houver, a tag ou o `id` envolvido. Nunca derruba o programa e nunca altera o arquivo. |
| RNF-15 | **Tolerância na leitura, como o TerraER:** aceitar declaração `<?xml?>`, indentação, UTF-8 direto, `id` ausente ou que não seja hexadecimal, e `DOCTYPE` (ignorado sem buscar DTD nem processar entidades; um `DOCTYPE` com subconjunto interno é recusado por segurança, RNF-10). Atributos e chaves de estilo desconhecidos são ignorados. |
| RNF-16 | **Tipo de atributo inválido.** Um `attributeType` fora dos cinco valores válidos é aceito na leitura, com aviso ao usuário, e tratado como o tipo padrão do elemento; o HaradaER nunca grava valor inválido. |
| RNF-13 | **Reimplementação independente.** O HaradaER não copia código, ícones, imagens nem textos do `TerraER3.14.jar`; o jar é só fonte de consulta e não é distribuído com o projeto. O formato de arquivo é compatível, mas a implementação é nova. Segundo o autor, o TerraER é distribuído sob GPLv3 (com menções a donationware / software livre acadêmico); isso não pôde ser verificado no `.jar`, que não contém texto de licença (`INVESTIGACOES.md` seção 9). Copiar ou traduzir código do TerraER implicaria GPLv3 para o HaradaER; a reimplementação independente evita isso. |

## 7. Critérios de aceitação da compatibilidade

1. **Golden files.** O HaradaER lê `amostra-basica.xml` e `amostra-todos-os-tipos.xml` e regrava um arquivo **semanticamente igual** (mesmos elementos, ids, referências e valores; ordem dos filhos de `<a>` pode variar).
2. **Ida e volta pelo TerraER.** Para cada arquivo gravado pelo HaradaER, as classes do TerraER (`harness/Gen2.java`, modo `read`) conseguem lê-lo e regravá-lo sem exceção, com o mesmo número de figuras.
3. **Abertura na interface do TerraER.** Verificação manual: abrir cada golden file e cada arquivo de teste do HaradaER no TerraER 3.14 e conferir que o diagrama é idêntico.
4. **Fuzz de estrutura.** Modelos gerados com todos os tipos e todas as conexões válidas da seção 5 passam nos critérios 1 e 2.

## 8. Questões em aberto

Detalhes e evidências em `INVESTIGACOES.md`.

| ID | Questão | Estado |
|---|---|---|
| QA-01 | Tamanho da figura vs. texto | **Investigada.** Forma cresce até texto + 20 e nunca encolhe; texto centralizado. Comportamento ao arrastar alças não medido. Medir texto sem a fonte do Java fica como diferença aceita (decisão 8) |
| QA-02 | Cardinalidade editada | **Resolvida.** `1` e `N` são fixos pela tag e não editáveis; só o rótulo de generalização é editável (`labelGeneralizacaoText`) |
| QA-03 | Direção de `lcaf` | **Resolvida.** O TerraER aceita as duas direções (validação simétrica e DDL com os dois casos). O HaradaER lê as duas e grava atributo→dono |
| QA-04 | Regras de DDL | **Investigada**; DDL adiado para depois da v1 (RF-13) |
| QA-05 | Estilos padrão | **Resolvida** para estilo; tamanhos de criação **inferidos** do bytecode (seção 5 de `INVESTIGACOES.md`) |
| QA-06 | Leitura de `attributeType` | **Resolvida.** Ver seção 3.3 |
| QA-07 | Tag desconhecida | **Resolvida.** O TerraER recusa o arquivo (RNF-02) |
| QA-08 | Modo de Edição Rápida | **Investigada** (inferida do bytecode); adiado para depois da v1 (RF-20) |
| QA-09 | Instrução SQL | **Resolvida.** Só no atributo derivado, gravada em `sql`; leitura e gravação na v1, edição adiada |
| QA-10 | Licença do TerraER | Informada pelo autor (GPLv3); não verificável no `.jar` |
| QA-11 | Gestos no Windows, macOS e X11; ctrl + rolagem | **Fora da v1 (decisão do autor):** a v1 considera só esta máquina (Linux/Wayland). Ctrl + rolagem como atalho de zoom está implementado (`gui/view.py`) |
| QA-12 | Versão mínima do Python e do PySide6 | **Decidida (autor):** a v1 mira só Python 3.14 e PySide6 6.12, as versões instaladas e verificadas nesta máquina. Não haverá piso em Python 3.11; versões mais antigas ficam sem suporte declarado |
| QA-13 | Copiar e colar com o TerraER | **Descartada (decisão do autor em 2026-10-22):** só o arquivo é compatível; a área de transferência do TerraER não será feita |
| QA-14 | GIF | **Descartada (decisão do autor em 2026-10-22):** exportar PNG, JPG, SVG e PDF; o PNG cobre a necessidade |

## 9. Material de referência

- `docs/referencia-terraer/amostra-basica.xml`: 2 entidades, 1 relacionamento, 2 atributos, conexões `llabelUm`, `llabelMuitos` e `lcaf`.
- `docs/referencia-terraer/amostra-todos-os-tipos.xml`: um exemplar de cada elemento e de cada conexão.
- `docs/INVESTIGACOES.md`: resultados das investigações sobre o comportamento do TerraER (QA-01 a QA-14), com as decisões que elas abrem.
- `docs/referencia-terraer/amostra-estilos.xml`: cor e espessura do traço, tracejado, cores com transparência, fonte, itálico e sublinhado.
- `docs/referencia-terraer/imagens/`: desenhos que o próprio TerraER exportou das amostras, para comparação visual.
- `docs/referencia-terraer/amostra-escapes-e-numeros.xml`, `amostra-numeros.xml`, `amostra-unicode.xml` e `amostra-vazios.xml`: caracteres especiais, números extremos, emoji e valores vazios.
- `docs/referencia-terraer/amostra-ordem-empilhamento.xml`: conexões antes dos nós (dono inline e `ref`).
- `docs/referencia-terraer/amostra-figuras-de-apoio.xml`: texto livre, formas, linhas, bézier, grupo e imagem.
- `docs/referencia-terraer/amostra-caracteres-invalidos.xml`: caracteres de controle que o TerraER grava e o XML puro recusa (o HaradaER devolve erro claro).
- `docs/referencia-terraer/ddl-saida-terraer.txt`, `matriz-validacao.txt` e `leitura-casos/`: saídas brutas das investigações.
- `docs/referencia-terraer/amostra-paralelas.xml` e `amostra-paralelas-dupla.xml`: três conexões "N" entre o mesmo par, feitas pela ferramenta de conexão do TerraER (desvio e letras N, M, P).
- `docs/referencia-terraer/criados-no-haradaer/`: arquivos criados pelos comandos do HaradaER, o que o TerraER regravou deles e as imagens dos dois programas (evidência do RNF-01 e do critério 4).
- `docs/referencia-terraer/harness/`: programas Java que usam o `TerraER3.14.jar` para gerar as amostras e medir a validação. Para reproduzir: extrair o `TerraER3.14.jar` numa pasta `jar/` (que contém também `swing-layout.jar`, `MRJAdapter.jar` e `appframework-0.42.jar`), então `javac -cp "jar:jar/swing-layout.jar:jar/MRJAdapter.jar:jar/appframework-0.42.jar" -d out harness/*.java` e `java -Djava.awt.headless=true -cp "out:<mesmo classpath>" Gen2 write saida.xml` (ou `Gen2 read entrada.xml saida.xml`, ou `Matrix`).

## 10. Estado da v1 (revisão de 2026-10-20)

Conferência de cada requisito com o programa e os testes (736 testes automáticos). Na revisão, o autor decidiu implementar copiar/colar/duplicar e agrupar (RF-03) e deixar para depois da v1 a paleta como painel (RNF-09); o painel Mensagens entrou depois, na mesma revisão. Em 2026-10-22 o autor trouxe a opção de inglês (RNF-06) de volta para a v1 e descartou a impressão (RF-14), o GIF (QA-14) e copiar e colar com o TerraER (QA-13).

**Requisitos funcionais**

| ID | Estado | Onde / observação |
|---|---|---|
| RF-01 | Pronto | Novo, abrir, salvar, salvar como, abrir recente (M4, M5d) |
| RF-02 | Pronto | Os 13 elementos e as 9 conexões na barra (M4) |
| RF-03 | Pronto | Mover, redimensionar, excluir, copiar, recortar, colar (também entre janelas), duplicar, agrupar e desagrupar |
| RF-04 | Pronto | Nome e rótulo da generalização: no desenho e em Propriedades |
| RF-05 | Pronto | Tipo SQL e anulabilidade em Propriedades (M5c) |
| RF-06 | Pronto | Desfazer e refazer de toda edição |
| RF-07 | Pronto | Zoom, grade, alinhar, frente/trás, selecionar do mesmo tipo (M3, M5b) |
| RF-08 | Pronto | Localizar (Ctrl+F) no inspetor (M5c) |
| RF-09 | Pronto | Conexões com problema em vermelho, liga/desliga em Exibir (M5a); avisos de estrutura em laranja, também com liga/desliga |
| RF-10 | Pronto | Conexões aceitas entre dois elementos (negrito na barra) e pares aceitos de um tipo (barra de status) (M5a) |
| RF-11 | Pronto | PNG, JPG, SVG, PDF e copiar como imagem (M5d) |
| RF-12 | Pronto | Figuras de apoio regravadas iguais (testes de ida e volta) |
| RF-13 | Fora da v1 | DDL |
| RF-14 | Descartado | Impressão (decisão do autor em 2026-10-22) |
| RF-15 | Pronto | Pinça e rolagem com dois dedos, testados pelo autor no Linux/Wayland (M3) |
| RF-16 | Pronto | Inspetor de objetos (M5c) |
| RF-17 | Pronto | Pergunta ao fechar; mensagens claras ao não conseguir gravar (M4, M5a) |
| RF-18 | Pronto | Campo de nome sobre o elemento (M4) |
| RF-19 | Pronto | Uma janela por documento |
| RF-20 | Pronto (parte da v1) | `sql` lido e regravado; edição fora da v1 |

Além do pedido: edição dos vértices das conexões e reconexão de pontas (`INVESTIGACOES.md` seção 16) e desvio automático das conexões repetidas (seção 15).

**Requisitos não funcionais**

| ID | Estado | Onde / observação |
|---|---|---|
| RNF-01 | Pronto | Ida e volta idêntica byte a byte com as amostras do TerraER; arquivos criados no HaradaER regravados pelo TerraER sem mudar o modelo (`criados-no-haradaer/`) |
| RNF-02, 03, 04, 05 | Pronto | Leitura e gravação (M1) |
| RNF-06 | Pronto | Trazido de volta para a v1 em 2026-10-22. Exibir › Idioma (português ou inglês; na primeira vez, o do sistema), com aviso de que vale ao reabrir; nomes padrão no idioma; manual `GETTING-STARTED.md` (`ARQUITETURA.md` seção 5.7) |
| RNF-07 | Pronto | Python 3.14, PySide6 6.12, Linux/Wayland |
| RNF-08 | Pronto | Núcleo sem Qt, conferido por teste |
| RNF-09 | Parcial; **o resto fica fora da v1 (decisão do autor)** | Painéis acopláveis (inspetor, propriedades e mensagens) com disposição lembrada. O painel Mensagens lista os erros de conexão e os avisos de estrutura, e escolher um leva ao elemento; a barra de status resume a verificação. Fica para depois da v1 (decisão do autor em 2026-10-22, depois de ver uma maquete): a paleta como opção, sem substituir a faixa. Exibir › Paleta escolhe entre **No alto** (a faixa de hoje) e **À esquerda** (painel acoplado em duas colunas, com Elementos e Conexões). As duas usam as mesmas ações; o destaque das conexões aceitas (RF-10) vale nas duas; o painel não fecha nem solta, para nunca ficar sem ferramentas |
| RNF-10, 14, 15 | Pronto | Leitura segura e erros claros (M1) |
| RNF-11 | Pronto | Gravação por arquivo temporário, mantendo as permissões do arquivo |
| RNF-12 | Pronto | 736 testes, sem tela |
| RNF-13 | Pronto | Nada copiado do `.jar` |
| RNF-16 | Pronto | Corrigido na revisão: tipo inválido avisa ao abrir e vira o tipo padrão |

**Critérios de aceitação (seção 7)**

| Critério | Estado |
|---|---|
| 1. Golden files | Pronto: todas as amostras regravadas idênticas |
| 2. Ida e volta pelo TerraER | Pronto: `RegravaTerra.java` lê e regrava os arquivos do HaradaER sem exceção e com o mesmo modelo |
| 3. Abertura na interface do TerraER | Feito pelo autor nos testes manuais de cada marco |
| 4. Fuzz de estrutura | Pronto: `criados-no-haradaer/todas-validas.xml`, com as 343 combinações aceitas, passa pelo TerraER e nenhuma conexão fica vermelha na validação dele |

