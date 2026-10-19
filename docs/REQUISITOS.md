# HaradaER — Documento de Requisitos

Versão 0.2 · 2026-10-19 · Rascunho

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
- Geração de DDL SQL.
- Interface Qt com painéis acopláveis e gestos de trackpad (RNF-09, RF-15).

**Fora do escopo (v1):**
- Banco de dados real, engenharia reversa a partir de SQL, edição colaborativa.
- Qualquer extensão do formato que o TerraER não leia (ver RNF-02).
- Interface de linha de comando (RNF-08).

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
| Atributo chave parcial | `atrchaveparcial` | Texto em negrito, contorno tracejado. Tem tipo e anulabilidade. |
| Atributo derivado | `atrderivado` | Elipse tracejada. **Sem** tipo nem anulabilidade. |
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

Os rótulos `1` e `N` são **implícitos na tag**; o arquivo não grava texto para eles.

### 3.3 Tipos de atributo

Gravados no atributo XML `attributeType` com o **tipo SQL**, não com o nome do tipo:

| Tipo no TerraER | Valor gravado | Observação |
|---|---|---|
| CHAR | `CHAR(128)` | |
| TEXT | `VARCHAR2(128)` | |
| INTEGER | `NUMBER` | Mesmo valor gravado de NUMBER. |
| NUMBER | `NUMBER(9,2)` | |
| DATE | `DATE` | |

> **Atenção.** No enum do TerraER, `INTEGER` tem tipo SQL `NUMBER` e `NUMBER` tem `NUMBER(9,2)`. Um atributo chave novo (tipo padrão INTEGER) foi gravado como `attributeType="NUMBER"` nas amostras. O HaradaER deve gravar exatamente esses valores, sem "corrigi-los" (RNF-03). Como o TerraER relê o valor `NUMBER` (INTEGER ou outro) ainda não foi verificado (QA-06).

`nullable` é `true` ou `false`.

## 4. Formato do arquivo (resumo normativo)

Detalhes completos nas amostras de `docs/referencia-terraer/`.

### 4.1 Estrutura

- Codificação **UTF-8**, **sem** declaração `<?xml ...?>` e **sem** DOCTYPE.
- Uma única linha, **sem indentação**.
- Raiz `<drawing>` → filho `<figures>` → uma figura por filho, na ordem de empilhamento (z-order).
- Extensão `.xml`.

### 4.2 Identificadores e referências

- Todo objeto recebe `id="<hex>"`, sequencial em ordem de escrita, a partir de `0`, em hexadecimal minúsculo (`0`…`f`, `10`, `1a`…).
- Uma referência a objeto já escrito usa `<tag ref="<id>"/>`. Exemplo: `<Owner><ent ref="0"/></Owner>`.

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

- A conexão referencia os dois nós por `Owner` + `ref`; os nós precisam estar **antes** da conexão no arquivo.
- O conector é `rConnector` nas amostras (retangular). Existem também `ellipseConnector`, `diamondConnector` e `bezierConnector`; devem ser lidos.

### 4.5 Tolerâncias observadas

- A **ordem** dos filhos dentro de `<a>` não é significativa: o TerraER relê e regrava em outra ordem (teste de ida e volta).
- Textos padrão de novos elementos mudam com o idioma (inglês em headless: `rel. 0`, `W. ENT. 0`, `key att. 0`; o jar tem `Labels_pt`). O texto gravado é o do usuário, então o idioma não afeta a compatibilidade.

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
| `atr` | `atr` (atributo composto) |

> A tabela de `lcaf` reflete a medição bruta, que também aceitou combinações na direção atributo→dono (por exemplo `atr→ent`, `atrchave→entrel`, `atrchaveparcial→entfraca`). Fica aberto confirmar se alguma é artefato da medição (QA-03).

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
| RF-09 | Verificação do modelo: destacar em vermelho as conexões inválidas (seção 5), com opção de ligar e desligar. |
| RF-10 | Recomendação de conexão entre dois elementos selecionados (e dos elementos possíveis para uma conexão). |
| RF-11 | Exportar para imagem (PNG, JPG, GIF) e copiar o modelo para a área de transferência. |
| RF-12 | Preservar sem alteração figuras e atributos desconhecidos ou de apoio lidos de um arquivo (texto livre, formas, imagens), regravando-os iguais. |
| RF-13 | Gerar o DDL SQL do modelo e exibi-lo, com opção de copiar. A análise do TerraER confirmou `CREATE TABLE`, colunas e `NOT NULL`; chaves primárias/estrangeiras e o mapeamento dos relacionamentos **não foram verificados** (QA-04). |
| RF-14 | **(Desejável)** Imprimir. Pode ficar para depois da v1. |
| **RF-15** | **Gestos de trackpad (obrigatório).** Na área do diagrama: pinça com dois dedos para zoom e rolagem com dois dedos para mover a visão. O zoom e a rolagem por teclado e menu continuam disponíveis como alternativa. Teste em Linux/Wayland com PySide6 6.12.0 confirmou: o zoom chega como `QNativeGestureEvent` do tipo `ZoomNativeGesture` (591 eventos, valores de -0,043 a +0,059 por evento, que se acumulam na escala) e a rolagem como `QWheelEvent` com `pixelDelta` e fases `ScrollBegin`/`ScrollUpdate` (145 eventos). A API `QPinchGesture` **não** disparou no Wayland; usar o evento nativo. Windows e macOS ainda precisam do mesmo teste (QA-11). |
| RF-16 | Inspetor de objetos: painel com a lista/árvore dos elementos do modelo, que permite selecionar um elemento e localizá-lo no diagrama (o TerraER tem o "Inspetor de Objetos"). |
| RF-17 | Perguntar se deseja salvar as alterações ao fechar um documento modificado ou sair (Salvar / Não salvar / Cancelar), e mostrar mensagem clara quando não for possível gravar o arquivo. |
| RF-18 | Edição do nome diretamente sobre o elemento (campo de texto flutuante), sem abrir diálogo. |
| RF-19 | Uma janela por documento (decisão do autor, igual ao TerraER): cada modelo abre na sua própria janela, com painéis, zoom e histórico de desfazer independentes, e vários modelos podem ficar abertos ao mesmo tempo. Sem abas. |
| RF-20 | Modo de Edição Rápida (`fastediting`) e instrução SQL por elemento ("Incluir respectiva instrução SQL"), ambos existentes no TerraER. O comportamento exato ainda não foi levantado (QA-08, QA-09); este requisito se completa depois dessa análise. |

### 6.2 Requisitos não funcionais

| ID | Requisito |
|---|---|
| **RNF-01** | **Compatibilidade bidirecional com o `.xml` do TerraER 3.14** (seção 1.1). |
| RNF-02 | O HaradaER **não deve gravar** tags, atributos ou metadados que o TerraER desconheça. A fábrica do TerraER só conhece as tags da seção 3 (`IllegalArgumentException` para classes fora dela na escrita); o comportamento na leitura de tag desconhecida não foi testado (QA-07), então a regra é conservadora. Qualquer dado extra do HaradaER fica em arquivo separado, nunca dentro do `.xml`. |
| RNF-03 | Reproduzir quirks do formato, como `INTEGER` gravado como `NUMBER` (seção 3.3), sem "corrigi-los". |
| RNF-04 | Leitura tolerante: aceitar qualquer ordem de filhos em `<a>`, com ou sem quebras de linha, e ids em qualquer ordem, desde que consistentes. |
| RNF-05 | Escrita conservadora: seguir a seção 4.1 (UTF-8, sem declaração XML, sem DOCTYPE). |
| RNF-06 | Interface em português, com opção de inglês, como o TerraER (`Labels_pt` / `Labels_en`). |
| RNF-07 | Rodar em Linux, Windows e macOS, em Python 3. |
| RNF-08 | Arquitetura em camadas: um **núcleo** (modelo, leitura/escrita do `.xml`, validação, DDL) que não importa nada de interface gráfica, e uma interface gráfica fina por cima. Isso permite testar a compatibilidade (seção 7) sem tela. Uma CLI é opcional e fica fora da v1 salvo decisão contrária. |
| RNF-09 | A interface gráfica usa **Qt**, o mesmo sistema do Octave, via **PySide6** (LGPL; funcionou no teste de gestos, Qt 6.12.0). Organização de janela como a do Octave: painéis acopláveis, redimensionáveis e que podem ser ocultados, em volta da área central do diagrama. Painéis previstos: paleta de elementos, inspetor de objetos (RF-16) e mensagens da verificação do modelo (RF-09). A disposição dos painéis é lembrada entre sessões. A lista de painéis é uma proposta a confirmar. |
| RNF-10 | **Abertura segura de arquivos recebidos.** O `.xml` pode vir de terceiros. A leitura não pode resolver entidades externas nem DTD, e deve limitar tamanho e profundidade, para evitar ataques de expansão de entidades e leitura de arquivos locais. Um arquivo inválido ou truncado gera mensagem de erro e **não** derruba o programa nem altera o arquivo. |
| RNF-11 | **Gravação segura.** Salvar escreve primeiro num arquivo temporário e só então substitui o original, para que uma falha no meio nunca corrompa um modelo existente. |
| RNF-12 | **Testes automatizados** do núcleo, sem tela: golden files, ida e volta e estrutura (seção 7). A verificação com as classes do TerraER exige um JDK, mas só nos testes, nunca para usar o HaradaER. |
| RNF-13 | **Reimplementação independente.** O HaradaER não copia código, ícones, imagens nem textos do `TerraER3.14.jar`; o jar é só fonte de consulta e não é distribuído com o projeto. O formato de arquivo é compatível, mas a implementação é nova. A licença do TerraER deve ser conferida antes de publicar o HaradaER (QA-10). |

## 7. Critérios de aceitação da compatibilidade

1. **Golden files.** O HaradaER lê `amostra-basica.xml` e `amostra-todos-os-tipos.xml` e regrava um arquivo **semanticamente igual** (mesmos elementos, ids, referências e valores; ordem dos filhos de `<a>` pode variar).
2. **Ida e volta pelo TerraER.** Para cada arquivo gravado pelo HaradaER, as classes do TerraER (`harness/Gen2.java`, modo `read`) conseguem lê-lo e regravá-lo sem exceção, com o mesmo número de figuras.
3. **Abertura na interface do TerraER.** Verificação manual: abrir cada golden file e cada arquivo de teste do HaradaER no TerraER 3.14 e conferir que o diagrama é idêntico.
4. **Fuzz de estrutura.** Modelos gerados com todos os tipos e todas as conexões válidas da seção 5 passam nos critérios 1 e 2.

## 8. Questões em aberto

| ID | Questão |
|---|---|
| QA-01 | Posição e tamanho exatos das figuras ao gravar: o TerraER recalcula tamanho a partir do texto? Definir se o HaradaER mede texto com a mesma fonte. |
| QA-02 | Como o TerraER grava rótulos de cardinalidade editados pelo usuário (as amostras não mostram `1`/`N` alterados). Requer teste na GUI. |
| QA-03 | Direção das ligações de atributo (`lcaf`): algumas combinações atributo→dono passaram na validação; confirmar quais o TerraER aceita ao desenhar. |
| QA-04 | Regras de geração de DDL (`GenerateTables`/`GenerateDDLAction`): mapeamento de relacionamentos 1:1, 1:N, N:N, generalização e atributos multivalorados. Requer análise dedicada antes do RF-13. |
| QA-05 | Estilos padrão (cores, fontes, espessuras) de cada elemento recém-criado, para o desenho do HaradaER ser visualmente igual ao do TerraER. |
| QA-06 | Como o TerraER interpreta `attributeType` ao reler (`NUMBER` vs `NUMBER(9,2)`). |
| QA-07 | Como o leitor do TerraER reage a tag ou atributo desconhecido (ignora ou falha). |
| QA-08 | O que faz o Modo de Edição Rápida (`FastEditingModeAction`). |
| QA-09 | A "instrução SQL" por elemento é gravada no `.xml`? Como (as amostras não têm), e como entra no DDL. |
| QA-10 | Licença e condições de uso do TerraER, para decidir como creditar e distribuir o HaradaER. |
| QA-11 | Gestos de trackpad no Windows e no macOS (só o Linux/Wayland foi testado), e comportamento no Linux/X11. Inclui ctrl + rolagem como atalho de zoom, que não foi exercitado no teste. |
| QA-12 | Versão mínima do Python e do PySide6 a suportar (o teste usou Python 3.14.8 e PySide6 6.12.0). |
| QA-13 | Copiar/colar entre HaradaER e TerraER: o TerraER usa um formato próprio de área de transferência (`Drawing-Clip`, tipo `image/x-jhotdraw`); decidir se o HaradaER deve ser compatível. |

## 9. Material de referência

- `docs/referencia-terraer/amostra-basica.xml`: 2 entidades, 1 relacionamento, 2 atributos, conexões `llabelUm`, `llabelMuitos` e `lcaf`.
- `docs/referencia-terraer/amostra-todos-os-tipos.xml`: um exemplar de cada elemento e de cada conexão.
- `docs/referencia-terraer/harness/`: programas Java que usam o `TerraER3.14.jar` para gerar as amostras e medir a validação. Para reproduzir: extrair o `TerraER3.14.jar` numa pasta `jar/` (que contém também `swing-layout.jar`, `MRJAdapter.jar` e `appframework-0.42.jar`), então `javac -cp "jar:jar/swing-layout.jar:jar/MRJAdapter.jar:jar/appframework-0.42.jar" -d out harness/*.java` e `java -Djava.awt.headless=true -cp "out:<mesmo classpath>" Gen2 write saida.xml` (ou `Gen2 read entrada.xml saida.xml`, ou `Matrix`).
