# ====================================================================
# PANDAS MODEL - Modelo de Tabela para QTableView
# ====================================================================
"""
Este arquivo contém a classe PandasModel, que serve como ponte
entre um DataFrame do Pandas e uma QTableView do PyQt6.
"""

import pandas as pd
from PyQt6.QtCore import QAbstractTableModel, Qt, QVariant


class PandasModel(QAbstractTableModel):
    """
    Modelo de tabela para integrar um DataFrame do Pandas com uma QTableView.
    """
    def __init__(self, data: pd.DataFrame):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)
        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])
        return QVariant()
