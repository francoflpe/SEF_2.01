#!/usr/bin/env python3
# ====================================================================
# MAIN - Ponto de Entrada da Aplicação
# ====================================================================
"""
Ponto de entrada principal da aplicação SEF - Software de Estudos Focus.
Configura e inicializa a aplicação Qt.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTranslator, QLibraryInfo, QLocale
from core.main_controller import MainController


def main():
    """
    Ponto de entrada principal da aplicação.
    Configura e executa o loop de eventos da Qt.
    """
    # Define o estilo visual "Fusion" para uma aparência consistente
    QApplication.setStyle("Fusion")
    
    # Criação da instância da aplicação Qt
    app = QApplication(sys.argv)
    
    # Configura a tradução para português do Brasil
    translator = QTranslator()
    translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if translator.load(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil), "qtbase", "_", translations_path):
        app.installTranslator(translator)
    
    # Criação e inicialização do Controller (que gerencia View e Model)
    controller = MainController()
    controller.show()
    
    # Início do loop de eventos da aplicação
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
