# HaradaER — Revisão teórica

Os pontos em que as regras do HaradaER ainda não seguem o livro de referência, **Elmasri e Navathe, *Sistemas de Banco de Dados*** (6ª edição em português), ou em que o livro deixa uma escolha em aberto.

Nada aqui está implementado; cada item espera uma decisão do autor (registrado em 2026-10-25). Os conceitos e as regras que já estão no programa estão em [CONCEITOS.md](CONCEITOS.md).

Cada item traz o que o livro diz, o que o HaradaER faz hoje, o impacto e uma recomendação com o esforço estimado.

## 1. Entidade fraca com participação parcial

- **Livro (seção 7.5):** "Um tipo de entidade fraca sempre tem uma restrição de participação total (dependência de existência) com relação a seu relacionamento de identificação".
- **HaradaER hoje:**
  - aceita a ligação da entidade fraca ao relacionamento de identificação com linha simples (participação parcial), sem avisar;
  - o aviso que existe é só o de fraca sem relacionamento de identificação (`core/rules/structure.py`, `check_structure`).
- **Impacto:**
  - só na verificação;
  - no esquema lógico, a fraca é mapeada do mesmo jeito.
- **Recomendação:** um aviso de estrutura novo, "entidade fraca com participação parcial no relacionamento de identificação". O arquivo não muda.
- **Esforço:** pequeno (um código de aviso, um texto e testes).

## 2. A tabela de conexões válidas veio do TerraER

- **Livro:** não tem uma tabela de pares válidos; as regras saem dos conceitos (caps. 7 e 8).
- **HaradaER hoje:**
  - as 343 combinações aceitas (`core/rules/tables.py`) foram medidas rodando o TerraER (`docs/referencia-terraer/matriz-validacao.txt`);
  - só as exceções de `BEYOND_TERRAER` (chave composta e multivalorado composto) foram tiradas do livro.
- **Impacto:**
  - pode haver par que o livro aceita e o HaradaER pinta de vermelho, ou o contrário;
  - exemplos a conferir: a subclasse que é entidade fraca ou associativa; a entidade associativa ligada à outra associativa; o atributo derivado como componente de um composto.
- **Recomendação:**
  - conferir par a par contra os caps. 7 e 8 e registrar cada diferença aqui;
  - mudar a tabela só com a aprovação de cada caso, porque mudanças afastam a verificação da do TerraER.
- **Esforço:** médio (é análise, mais do que código).

## 3. Nomes de papel no relacionamento recursivo

- **Livro (seção 7.7.1, Figura 7.2):** no relacionamento recursivo SUPERVISAO, a mesma entidade FUNCIONARIO aparece em dois papéis, supervisor e supervisionado. O mapeamento usa o papel no nome da coluna (`Cpf_supervisor`).
- **HaradaER hoje:**
  - o TerraER não tem nomes de papel, e o HaradaER também não;
  - no esquema lógico, a segunda coluna sai com número: `Cpf_FUNCIONARIO_2`.
- **Impacto:**
  - só nos nomes do esquema lógico (e do DDL, depois);
  - gravar o papel exigiria algo novo no `.xml`, e o TerraER poderia perder ou recusar.
- **Recomendação:**
  - deixar como está até haver um jeito de guardar o papel sem mexer no `.xml`;
  - uma opção é um arquivo à parte, como o `.esquema.md`, mas editável.
- **Esforço:** médio a grande.

## 4. Entidade associativa

- **Livro (seção 8.7.4, Agregação):**
  - o modelo EER do livro não tem agregação;
  - para representá-la corretamente no modelo ER, cria-se um tipo de entidade fraca identificado pelas entidades do relacionamento (Figura 8.11(e)).
- **HaradaER hoje:**
  - a entidade associativa (`entrel`) vem do TerraER, na notação de Heuser;
  - no esquema lógico, ela vira uma relação com uma chave estrangeira para cada entidade ligada a ela, que juntas formam a chave primária, como a entidade fraca da Figura 8.11(e);
  - a entidade associativa pode ter atributo-chave próprio: o TerraER aceita, e então ele vira a chave primária.
- **Impacto:** nenhum erro; é uma escolha de interpretação.
- **Recomendação:** manter, e confirmar com a referência da disciplina se a chave própria da associativa deve ser aceita.
- **Esforço:** pequeno.

## 5. Citações com a numeração da edição em inglês

- **HaradaER hoje:** os comentários do código citam o livro pela edição em inglês:
  - `core/rules/tables.py` e `core/rules/structure.py` citam "cap. 3" e "caps. 3 e 4";
  - os exemplos (`Registration(State, Number)`, `{PreviousDegrees ...}`) também vêm da edição em inglês.
- **Na edição em português:** o modelo ER é o cap. 7, e o EER é o cap. 8.
- **Recomendação:** trocar as citações e os exemplos pelos da edição em português.
- **Esforço:** pequeno (só comentários).

## 6. Notação (mín., máx.)

- **Livro (seção 7.7.4):** uma notação alternativa dá os números mínimo e máximo de participação, por exemplo (0, N) ou (1, 1). Ela permite valores como 4 ou 5, que a notação 1/N com linha simples ou dupla não expressa.
- **HaradaER hoje:**
  - não tem essa notação;
  - o TerraER também não, e o arquivo dele não tem onde guardá-la.
- **Recomendação:** não implementar. O próprio livro a apresenta como alternativa, e ela exigiria algo novo no `.xml`.
- **Esforço:** grande.

## 7. Escolhas do esquema lógico em que o livro deixa opções

O esquema lógico (RF-23) teve de escolher onde o livro oferece mais de uma forma. As escolhas estão em [CONCEITOS.md](CONCEITOS.md), seção 3.

| Ponto | O livro | O HaradaER | A decidir |
|---|---|---|---|
| Especialização (etapa 8) | Quatro opções: 8A, 8B, 8C e 8D | Sempre 8A, a que o livro diz servir em qualquer caso | Escolher a opção por especialização, ou pela restrição desenhada (8B para disjunta e total, 8C para disjunta, 8D para sobreposta) |
| 1:1 sem participação total ou com as duas (etapa 3) | A chave estrangeira vai do lado total, sem regra para o empate | Vai para a primeira entidade ligada | Manter, ou usar a técnica da relação mesclada quando as duas forem totais |
| Ligação direta entidade → entidade | Não trata | A origem é a superclasse | Confirmar com o desenho do TerraER |
| União (etapa 9) | Chave substituta na categoria | Supõe que as superclasses se ligam ao círculo pela linha de participação e a categoria pela generalização simples | Confirmar com um modelo de união desenhado no TerraER |
| Superclasse num círculo com ligações iguais | — | A única entidade com atributo-chave, com aviso | Manter, ou não mapear e só avisar |
| Uma entidade fraca ligada duas vezes à mesma dona | — | Não é tratada como fraca; o relacionamento vira uma relação comum | Confirmar se o caso faz sentido |
