"""Aviso de versão nova (RF-22): a consulta roda numa linha de execução à parte, para a janela
nunca esperar pela rede, e o resultado volta por sinal do Qt.

Desde a 1.4.0, o aviso também atualiza (Atualizar e reiniciar): `UpdateInstaller` prepara a
versão nova em segundo plano (`selfupdate.prepare`) e a troca acontece quando o programa fecha,
com nenhum documento aberto."""

from __future__ import annotations

import threading
from datetime import date

import shiboken6
from PySide6.QtCore import QObject, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog, QWidget

import haradaer
from haradaer import selfupdate, updates
from haradaer.gui.settings import last_update_check, set_last_update_check, update_check_enabled
from haradaer.i18n import _


class UpdateChecker(QObject):
    """Uma consulta por vez. `manual` diz se a pessoa pediu (Ajuda › Verificar atualizações):
    só então "já é a mais recente" e "não foi possível verificar" aparecem."""

    _done = Signal(object, bool, str)  # versão mais recente (ou None se falhou), manual, erro

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
        erro = ""
        try:
            versao = selfupdate.latest_version()
        except OSError as falha:
            versao, erro = None, str(falha)
        self._done.emit(versao, manual, erro)

    def _show(self, versao: str | None, manual: bool, erro: str = "") -> None:
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
            alvo = selfupdate.install_target()
            motivo = selfupdate.why_not(alvo)
            atualizar = None
            if motivo is None:
                atualizar = caixa.addButton(
                    _("Atualizar e &reiniciar"), QMessageBox.ButtonRole.AcceptRole
                )
            elif alvo is not None:  # do código-fonte, o motivo não interessa
                caixa.setInformativeText(motivo)
            baixar = caixa.addButton(_("&Baixar"), QMessageBox.ButtonRole.ActionRole)
            caixa.addButton(_("Agora &não"), QMessageBox.ButtonRole.RejectRole)
            caixa.exec()
            if caixa.clickedButton() is baixar:
                QDesktopServices.openUrl(QUrl(updates.RELEASES))
            elif atualizar is not None and caixa.clickedButton() is atualizar:
                assert alvo is not None
                installer().start(versao, alvo, pai)
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
                _("Não foi possível verificar agora (sem internet ou o GitHub não respondeu).")
                + (f"\n\n{erro}" if erro else ""),  # o motivo técnico ajuda a diagnosticar
            )


class UpdateInstaller(QObject):
    """Uma atualização por vez para o programa todo (as janelas compartilham)."""

    _progress = Signal(int, int)
    _done = Signal(object, str)  # Prepared (ou None se falhou), erro

    def __init__(self) -> None:
        super().__init__()
        self.prepared: selfupdate.Prepared | None = None
        self.restart_on_quit = False
        self._running = False
        self._cancel = False
        self._dialog: QProgressDialog | None = None
        self._parent: QWidget | None = None
        self._progress.connect(self._show_progress)
        self._done.connect(self._finished)

    def start(self, versao: str, alvo: selfupdate.Target, pai: QWidget | None = None) -> bool:
        if self._running or self.prepared is not None:
            return False
        self._running, self._cancel, self._parent = True, False, pai
        self._dialog = QProgressDialog(
            _("Baixando o HaradaER {versao}…").format(versao=versao), _("Cancelar"), 0, 100, pai
        )
        self._dialog.setWindowTitle(_("Atualizações"))
        self._dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._dialog.setMinimumDuration(0)
        self._dialog.canceled.connect(self._cancelar)
        self._dialog.setValue(0)
        threading.Thread(target=self._prepare, args=(versao, alvo), daemon=True).start()
        return True

    def _cancelar(self) -> None:
        self._cancel = True

    def _prepare(self, versao: str, alvo: selfupdate.Target) -> None:
        try:
            pronto = selfupdate.prepare(
                versao, alvo, lambda f, t: self._progress.emit(f, t), lambda: self._cancel
            )
        except selfupdate.UpdateError as erro:
            self._done.emit(None, str(erro))
        except Exception as erro:  # noqa: BLE001 (a linha de execução não pode morrer calada)
            self._done.emit(None, f"{type(erro).__name__}: {erro}")
        else:
            self._done.emit(pronto, "")

    def _show_progress(self, feito: int, total: int) -> None:
        if self._dialog is None:
            return
        if total and feito < total:
            self._dialog.setValue(int(feito * 100 / total))
        else:  # baixado: falta conferir e testar, sem medida de andamento
            self._dialog.setLabelText(_("Conferindo a versão nova…"))
            self._dialog.setRange(0, 0)

    def _finished(self, pronto: selfupdate.Prepared | None, erro: str) -> None:
        self._running = False
        if self._dialog is not None:
            self._dialog.canceled.disconnect(self._cancelar)
            self._dialog.close()
            self._dialog = None
        pai = self._parent
        if pai is not None and not shiboken6.isValid(pai):
            pai = None
        if pronto is None:
            if not self._cancel:
                QMessageBox.warning(pai, _("Atualizações"), erro)
            return
        self.prepared = pronto
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.apply_on_quit)
        caixa = QMessageBox(pai)
        caixa.setIcon(QMessageBox.Icon.Information)
        caixa.setWindowTitle(_("Atualizações"))
        caixa.setText(_("O HaradaER {versao} está pronto.").format(versao=pronto.versao))
        caixa.setInformativeText(
            _("Se continuar agora, a atualização é instalada quando você fechar o HaradaER.")
        )
        reiniciar = caixa.addButton(_("&Reiniciar agora"), QMessageBox.ButtonRole.AcceptRole)
        caixa.addButton(_("Ao &fechar"), QMessageBox.ButtonRole.RejectRole)
        caixa.exec()
        if caixa.clickedButton() is reiniciar:
            self.restart_now()

    def restart_now(self) -> None:
        """Fecha as janelas (cada uma pergunta se quer salvar). Se alguma ficar aberta, a
        troca fica para quando o programa fechar."""
        self.restart_on_quit = True
        QApplication.closeAllWindows()
        if any(w.isVisible() for w in QApplication.topLevelWidgets()):
            self.restart_on_quit = False

    def apply_on_quit(self) -> None:
        pronto, self.prepared = self.prepared, None
        if pronto is None:
            return
        try:
            selfupdate.apply(pronto)
        except selfupdate.UpdateError as erro:
            QMessageBox.warning(None, _("Atualizações"), str(erro))
            return
        if self.restart_on_quit:
            selfupdate.restart(pronto.alvo)


_installer: UpdateInstaller | None = None


def installer() -> UpdateInstaller:
    global _installer
    if _installer is None:
        _installer = UpdateInstaller()
    return _installer
