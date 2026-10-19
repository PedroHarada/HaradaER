"""Erros do núcleo."""


class ArquivoInvalidoError(ValueError):
    """O arquivo não pode ser aberto como modelo do TerraER (RNF-14).

    A mensagem diz o problema em português; `linha` é a linha do XML quando se sabe.
    """

    def __init__(self, mensagem: str, linha: int | None = None):
        self.mensagem = mensagem
        self.linha = linha
        super().__init__(f"{mensagem} (linha {linha})" if linha else mensagem)
