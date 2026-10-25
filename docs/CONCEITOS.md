# HaradaER — Conceitos

Os conceitos de banco de dados que o HaradaER usa e vai usar, ligados ao livro de referência e ao que já está pronto no programa.

A base teórica é o livro **Elmasri e Navathe, *Sistemas de Banco de Dados*** (6ª edição em português, Pearson, 2011). As seções e as páginas abaixo são dessa edição. O TerraER 3.14 é a referência de formato de arquivo e de comportamento (RNF-01), não de teoria.

Os pontos em que o HaradaER ainda não segue o livro estão em [REVISAO-TEORICA.md](REVISAO-TEORICA.md).

## 1. Onde está cada assunto no livro

| Assunto | Onde | Usado em |
|---|---|---|
| Atributos (simples, composto, multivalorado, derivado), chaves | Cap. 7, seção 7.3 (atributo derivado, p. 136) | Elementos do diagrama, esquema lógico |
| Relacionamentos, razão de cardinalidade, participação | Cap. 7, seção 7.4 | Conexões, esquema lógico |
| Entidade fraca, chave parcial, relacionamento de identificação | Cap. 7, seção 7.5 (p. 144) | Elementos, avisos de estrutura, esquema lógico |
| Resumo da notação dos diagramas ER | Cap. 7, seção 7.7.1 (p. 146) | Desenho dos elementos |
| Especialização e generalização | Cap. 8, seções 8.2 e 8.3 (p. 163 em diante) | Círculos `d` e `o` |
| Categorias (tipos união) | Cap. 8, seção 8.4 | Círculo `u` |
| Agregação | Cap. 8, seção 8.7.4 (p. 178–179) | Entidade associativa |
| Mapeamento ER/EER para relacional | Cap. 9 (p. 189–199) | Esquema lógico (RF-23) |
| `CREATE TABLE`, `PRIMARY KEY`, `FOREIGN KEY` | Cap. 4, Figura 4.1 (p. 60–61) | DDL (planejado) |
| Views (`CREATE VIEW`) | Cap. 5, seção 5.3.2 | DDL do atributo derivado (planejado) |

## 2. Os elementos do diagrama

A notação do HaradaER é a do TerraER, que é a mesma do livro (seção 7.7.1). Cada elemento tem uma tag no arquivo `.xml`.

| No diagrama | Tag | Conceito no livro | No HaradaER hoje |
|---|---|---|---|
| Retângulo | `ent` | Tipo de entidade regular (forte) | Pronto |
| Retângulo duplo | `entfraca` | Tipo de entidade fraca (7.5) | Pronto |
| Losango | `rel` | Tipo de relacionamento (7.4) | Pronto |
| Losango duplo | `relfraco` | Relacionamento de identificação (7.5) | Pronto |
| Retângulo com losango | `entrel` | Entidade associativa. Não existe com esse nome no livro: é a agregação da seção 8.7.4, que o livro representa como uma entidade fraca identificada pelas entidades do relacionamento (Figura 8.11(e)) | Pronto |
| Oval | `atr` | Atributo simples; ligado a outro atributo, componente de um atributo composto | Pronto, com tipo SQL e anulável |
| Oval com nome sublinhado | `atrchave` | Atributo-chave | Pronto; com componentes, chave composta |
| Oval com sublinhado tracejado | `atrchaveparcial` | Chave parcial da entidade fraca | Pronto |
| Oval dupla | `atrmulti` | Atributo multivalorado | Pronto |
| Oval pontilhada | `atrderivado` | Atributo derivado: não é armazenado, é calculado (7.3) | Pronto; a instrução SQL é lida e regravada, mas ainda não editável |
| Círculo `d` | `disjuncao` | Especialização disjunta (8.3) | Pronto |
| Círculo `o` | `sobreposicao` | Especialização sobreposta (8.3) | Pronto |
| Círculo `u` | `uniao` | Categoria, ou tipo união (8.4) | Pronto |

As conexões dizem a razão de cardinalidade e a participação:

| Conexão | Conceito |
|---|---|
| Lado 1, Lado N | Razão de cardinalidade 1 ou N; participação parcial (linha simples) |
| Total 1, Total N | Razão de cardinalidade 1 ou N; participação total (linha dupla), também chamada de dependência de existência |
| Lig. atrib. | Liga um atributo ao seu dono (entidade, relacionamento ou atributo composto) |
| Participação opcional/obrigatória em generalização | Liga a superclasse ao círculo; a obrigatória (linha dupla) é a especialização total |
| Generalização simples | Liga o círculo à subclasse, ou uma entidade direto à subclasse quando há uma só |

## 3. O esquema lógico relacional (RF-23)

O HaradaER calcula o esquema relacional a partir do diagrama, segue o algoritmo do capítulo 9 e mostra o resultado no painel **Esquema lógico**. Com a opção **Arquivo › Gravar esquema lógico ao salvar** ligada, o mesmo texto vai para `<modelo>.esquema.md`, ao lado do `.xml`.

O esquema nunca é gravado no `.xml`: ele é sempre refeito do desenho, e o arquivo continua igual ao do TerraER.

A notação é a do livro, `RELACAO (chave, atributo, ...)`. Como o Markdown básico não tem sublinhado, a chave primária vai em **negrito**. As chaves estrangeiras ficam listadas abaixo de cada relação.

### 3.1 Regras, etapa por etapa

| Etapa do livro | O que o HaradaER faz |
|---|---|
| 1. Entidade regular | Uma relação com os atributos simples. Um atributo composto entra como os seus componentes simples. A chave primária é o atributo-chave; um atributo-chave com componentes vira uma chave composta. |
| 2. Entidade fraca | A relação recebe a chave primária da dona como chave estrangeira. A chave primária é a chave da dona mais a chave parcial. A dona pode ser também uma entidade fraca, e as chaves passam em cadeia. Os atributos do relacionamento de identificação vão para a fraca. |
| 3. Relacionamento 1:1 | Técnica da chave estrangeira: ela vai para a entidade com participação total. Se as duas forem totais, ou nenhuma, vai para a primeira ligada ao relacionamento. Os atributos do relacionamento vão junto. |
| 4. Relacionamento 1:N | A chave estrangeira vai para a entidade do lado N, mais os atributos do relacionamento. Ela pode ser nula se a participação do lado N for parcial. |
| 5. Relacionamento N:N | Uma relação nova, com o nome do relacionamento. As chaves estrangeiras para as duas entidades formam a chave primária. Os atributos do relacionamento entram nela. |
| 6. Atributo multivalorado | Uma relação nova, `<DONO>_<ATRIBUTO>`. A chave primária é a chave da dona mais o valor; um multivalorado composto entra com todos os componentes. |
| 7. Relacionamento n-ário | Uma relação nova com uma chave estrangeira para cada entidade. A chave primária são as do lado N; as do lado 1 ficam fora da chave, como manda o livro. |
| 8. Especialização | Opção 8A: a subclasse recebe a chave da superclasse, que é ao mesmo tempo a sua chave primária e uma chave estrangeira para a superclasse. O livro diz que essa opção funciona para qualquer especialização: total ou parcial, disjunta ou sobreposta. |
| 9. Categoria (união) | A categoria ganha uma chave substituta, `Id_<CATEGORIA>`. Cada superclasse recebe essa chave como chave estrangeira. |
| Agregação (8.7.4) | A entidade associativa vira uma relação com uma chave estrangeira para cada entidade ligada a ela. Sem atributo-chave próprio, a chave primária são as do lado N (ou todas), como na entidade fraca da Figura 8.11(e). Quando ela participa de outro relacionamento, a chave dela é referenciada como a de uma entidade. |
| Atributo derivado (7.3) | Não vira coluna. Aparece numa seção própria, com a instrução SQL que calcula o valor, se houver. |

### 3.2 Nomes

- **Relação:** o nome do elemento em maiúsculas, com espaços trocados por `_`, como no TerraER.
- **Coluna:** o nome do atributo, com espaços trocados por `_`.
- **Chave estrangeira:** `<atributo>_<RELACAO>`, por exemplo `Cpf_FUNCIONARIO`. Uma chave que já veio de outra relação não acumula sufixos: `Id_maquina_PROMPT`, e não `Id_maquina_MAQUINA_SESSAO_PROMPT`.
- **Na especialização e na categoria:** a chave mantém o nome da superclasse, ou da categoria, como no livro.
- **Nomes repetidos:** ganham `_2`, `_3`. É o caso do relacionamento recursivo, em que a mesma entidade aparece duas vezes.

O livro renomeia algumas colunas à mão: `Dnr` em vez de `Dnumero_DEPARTAMENTO`, e `Cpf_supervisor` no recursivo. O HaradaER não tem como saber esses nomes, porque o diagrama do TerraER não guarda nomes de papel ([REVISAO-TEORICA.md](REVISAO-TEORICA.md), item 3).

### 3.3 Avisos

O esquema lista, no fim, os avisos de estrutura do modelo, por exemplo uma entidade sem atributo-chave. Também lista o que ficou incompleto no mapeamento:
- uma relação sem chave primária;
- uma chave estrangeira que não pôde ser criada, porque a relação referenciada não tem chave;
- uma generalização em que a superclasse foi deduzida, porque todas as ligações do círculo eram do mesmo tipo e a superclasse foi tomada como a única entidade com atributo-chave.

### 3.4 Exemplo

O banco EMPRESA do livro (Figura 9.1) gera, no HaradaER:

```
FUNCIONARIO (**Cpf**, Pnome, Minicial, Unome, Datanasc, Endereco, Sexo, Salario, Dnumero_DEPARTAMENTO, Cpf_FUNCIONARIO)
DEPARTAMENTO (**Dnumero**, Dnome, Cpf_FUNCIONARIO, Data_inicio)
PROJETO (**Projnumero**, Projnome, Projlocal, Dnumero_DEPARTAMENTO)
DEPENDENTE (**Cpf_FUNCIONARIO**, **Nome_dependente**, Sexo, Datanasc, Parentesco)
TRABALHA_EM (**Cpf_FUNCIONARIO**, **Projnumero_PROJETO**, Horas)
DEPARTAMENTO_LOCALIZACOES (**Dnumero_DEPARTAMENTO**, **Localizacoes**)
```

São as mesmas relações e chaves da Figura 9.2, com os nomes gerados no lugar dos que o livro renomeou. Esse exemplo é conferido em `tests/core/test_esquema.py`.

## 4. O que vem depois

- **DDL em SQL (RF-13):** escrever o esquema lógico como `CREATE TABLE` (cap. 4). O tipo SQL e a anulabilidade de cada coluna já são guardados no esquema. O dialeto ainda é uma decisão a tomar: os tipos do arquivo (`VARCHAR2`, `NUMBER`) são do Oracle, e o livro usa os do SQL padrão.
- **Instrução SQL do atributo derivado (RF-20):** editar na tela a instrução que hoje só é lida e regravada. No DDL, ela vira uma view (seção 5.3.2), como no TerraER.
- **Modo de Edição Rápida (RF-20):** manter a ferramenta de criação depois de cada elemento. Hoje, segurar Shift já faz isso.

## 5. Glossário

- **Relação:** uma tabela do modelo relacional.
- **Chave primária:** os atributos que identificam cada tupla da relação.
- **Chave estrangeira:** atributos que referenciam a chave primária de outra relação.
- **Chave parcial:** o atributo que identifica uma entidade fraca entre as da mesma dona.
- **Chave substituta:** uma chave criada para identificar a categoria, quando as superclasses têm chaves diferentes.
- **Razão de cardinalidade:** o número máximo de participações (1 ou N).
- **Participação total:** toda entidade precisa participar do relacionamento (a cardinalidade mínima é 1); é a linha dupla.
- **Relação de relacionamento:** a relação criada para um relacionamento N:N ou n-ário.
- **View:** uma tabela virtual, definida por uma consulta.
