"""Erros do núcleo."""

from haradaer.i18n import _


class ArquivoInvalidoError(ValueError):
    """O arquivo não pode ser aberto como modelo do TerraER (RNF-14).

    A mensagem diz o problema no idioma da interface; `linha` é a linha do XML quando se sabe.
    """

    def __init__(self, mensagem: str, linha: int | None = None):
        self.mensagem = mensagem
        self.linha = linha
        super().__init__(
            _("{mensagem} (linha {linha})").format(mensagem=mensagem, linha=linha)
            if linha
            else mensagem
        )
