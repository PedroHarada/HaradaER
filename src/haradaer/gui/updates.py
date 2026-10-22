"""Aviso de versão nova (RF-22): a consulta roda numa linha de execução à parte, para a janela
nunca esperar pela rede, e o resultado volta por sinal do Qt."""

from __future__ import annotations

import threading
from datetime import date

import shiboken6
from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox, QWidget

import haradaer
from haradaer import updates
from haradaer.gui.settings import last_update_check, set_last_update_check, update_check_enabled
from haradaer.i18n import _


class UpdateChecker(QObject):
    """Uma consulta por vez. `manual` diz se a pessoa pediu (Ajuda › Verificar atualizações):
    só então "já é a mais recente" e "não foi possível verificar" aparecem."""

    _done = Signal(object, bool)  # versão mais recente (ou None se falhou), manual

    def __init__(self, parent_widget: QWidget | None = None) -> None:
        super().__init__()
        self.parent_widget = parent_widget
        self._running = False
        self._done.connect(self._show)

    def check(self, manual: bool) -> bool:
        if self._running:
            return False
        self._running = True
        threading.Thread(target=self._fetch, args=(manual,), daemon=True).start()
        return True

    def check_if_due(self, hoje: date | None = None) -> bool:
        """Ao abrir: se a verificação estiver ligada e ainda não tiver rodado hoje."""
        hoje = hoje or date.today()
        if not update_check_enabled() or not updates.due_today(last_update_check(), hoje):
            return False
        set_last_update_check(hoje.isoformat())
        return self.check(manual=False)

    def _fetch(self, manual: bool) -> None:
        try:
            versao = updates.fetch_latest()
        except OSError:
            versao = None
        self._done.emit(versao, manual)

    def _show(self, versao: str | None, manual: bool) -> None:
        self._running = False
        atual = haradaer.__version__
        pai = self.parent_widget
        if pai is not None and not shiboken6.isValid(pai):
            pai = None  # a janela fechou enquanto a consulta rodava
        if versao is not None and updates.is_newer(versao, atual):
            caixa = QMessageBox(pai)
            caixa.setIcon(QMessageBox.Icon.Information)
            caixa.setWindowTitle(_("Versão nova"))
            caixa.setText(
                _("O HaradaER {nova} está disponível (você tem a {atual}).").format(
                    nova=versao, atual=atual
                )
            )
            baixar = caixa.addButton(_("&Baixar"), QMessageBox.ButtonRole.AcceptRole)
            caixa.addButton(_("Agora &não"), QMessageBox.ButtonRole.RejectRole)
            caixa.exec()
            if caixa.clickedButton() is baixar:
                QDesktopServices.openUrl(QUrl(updates.RELEASES))
        elif manual and versao is not None:
            QMessageBox.information(
                pai,
                _("Atualizações"),
                _("Você já tem a versão mais recente ({atual}).").format(atual=atual),
            )
        elif manual:
            QMessageBox.information(
                pai,
                _("Atualizações"),
                _("Não foi possível verificar agora (sem internet ou o GitHub não respondeu)."),
            )
