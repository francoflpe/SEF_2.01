# ====================================================================
# BARRAS MODEL - Modelo Especializado para Dados de Barras
# ====================================================================
"""
TEMPLATE DE EXEMPLO - Este arquivo demonstra como criar modelos
especializados para tipos de dados específicos.

Para implementar um novo modelo:
1. Copie este template
2. Renomeie para {tipo_de_dado}_model.py
3. Customize os métodos conforme as necessidades do tipo
4. Importe no __init__.py do pacote data_models

Este modelo encapsula:
- Validações específicas do tipo de dado
- Cabeçalhos de tabela customizados
- Formatação de valores
- Widgets de edição especializados
- Cálculos e conversões
"""

from typing import Dict, List, Tuple, Optional
from PyQt6.QtWidgets import QWidget, QLineEdit, QComboBox


class BarrasModel:
    """
    Modelo especializado para dados do tipo 'barras'.
    
    Gerencia validação, formatação e widgets específicos
    para dados de barras elétricas.
    """
    
    # Tipo de dado que este modelo gerencia
    DATA_TYPE = "barras"
    
    # Nome de exibição
    DISPLAY_NAME = "Barras"
    
    def __init__(self):
        """Inicializa o modelo de barras."""
        self._cached_headers = None
    
    def get_column_headers(self) -> List[str]:
        """
        Retorna os cabeçalhos das colunas para exibição na tabela.
        
        Returns:
            Lista de strings com os nomes das colunas
        """
        if self._cached_headers is None:
            self._cached_headers = [
                "Tipo de Componente",
                "Tensão Nominal (V)",
                "Corrente Assimétrica 3P (A)",
                "Corrente Simétrica Inicial 3P (A)",
                "X/R Positivo",
                "Corrente Assimétrica SLG (A)",
                "Corrente Simétrica Inicial SLG (A)",
                "X/R SLG (pu)",
                "Nó/Barramento",
                "Descrição",
                "IEC909 Ikpp 3P (kA)",
                "IEC909 Ikpp SLG (kA)",
            ]
        return self._cached_headers
    
    def validate_field(self, field_name: str, value: str) -> Tuple[bool, str]:
        """
        Valida um campo específico.
        
        Args:
            field_name: Nome do campo
            value: Valor a ser validado
            
        Returns:
            Tupla (is_valid, error_message)
        """
        # Validações específicas por campo
        if field_name == "nominalVoltage":
            if not value or value.strip() == "":
                return False, "Tensão nominal é obrigatória"
            try:
                voltage = float(value)
                if voltage <= 0:
                    return False, "Tensão deve ser positiva"
            except ValueError:
                return False, "Tensão deve ser um número válido"
        
        elif field_name == "componentType":
            valid_types = ["Bus", "Generator", "Load", "Transformer"]
            if value not in valid_types:
                return False, f"Tipo deve ser um de: {', '.join(valid_types)}"
        
        # Validação genérica de números para campos numéricos
        numeric_fields = [
            "asym_halfcycle_3p", "init_sim_3p", "x-r_3p",
            "asym_halfcycle_slg", "init_sim_slg", "x-r_slg",
            "iec909_ikpp_3p", "iec909_ikpp_slg"
        ]
        if field_name in numeric_fields:
            if value and value.strip():
                try:
                    float(value)
                except ValueError:
                    return False, f"'{field_name}' deve ser um número válido"
        
        return True, ""
    
    def validate_data(self, data: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        Valida um dicionário completo de dados.
        
        Args:
            data: Dicionário com os dados do nó
            
        Returns:
            Tupla (is_valid, list_of_errors)
        """
        errors = []
        
        for field_name, value in data.items():
            is_valid, error_msg = self.validate_field(field_name, value)
            if not is_valid:
                errors.append(error_msg)
        
        # Validações de regras de negócio complexas
        if data.get("componentType") == "Generator":
            if not data.get("nominalVoltage"):
                errors.append("Geradores devem ter tensão nominal definida")
        
        return len(errors) == 0, errors
    
    def format_value(self, field_name: str, value: str) -> str:
        """
        Formata um valor para exibição.
        
        Args:
            field_name: Nome do campo
            value: Valor a ser formatado
            
        Returns:
            Valor formatado para exibição
        """
        # Formata tensões
        if field_name == "nominalVoltage" and value:
            try:
                voltage = float(value)
                if voltage >= 1000:
                    return f"{voltage/1000:.2f} kV"
                return f"{voltage:.0f} V"
            except ValueError:
                return value
        
        # Formata correntes (A → kA se >= 1000)
        current_fields = ["asym_halfcycle_3p", "init_sim_3p", "asym_halfcycle_slg", "init_sim_slg"]
        if field_name in current_fields and value:
            try:
                current = float(value)
                if current >= 1000:
                    return f"{current/1000:.2f} kA"
                return f"{current:.2f} A"
            except ValueError:
                return value
        
        return value
    
    def get_editor_widget(self, field_name: str, parent: Optional[QWidget] = None) -> QWidget:
        """
        Retorna um widget de edição customizado para o campo.
        
        Args:
            field_name: Nome do campo
            parent: Widget pai (opcional)
            
        Returns:
            Widget apropriado para editar o campo
        """
        # ComboBox para tipo de componente
        if field_name == "componentType":
            combo = QComboBox(parent)
            combo.addItems(["Bus", "Generator", "Load", "Transformer"])
            combo.setEditable(False)
            return combo
        
        # ComboBox para tensões nominais comuns
        if field_name == "nominalVoltage":
            combo = QComboBox(parent)
            common_voltages = ["220", "380", "440", "13800", "34500", "69000", "138000"]
            combo.addItems(common_voltages)
            combo.setEditable(True)  # Permite valores customizados
            return combo
        
        # LineEdit padrão para outros campos
        return QLineEdit(parent)
    
    def calculate_derived_values(self, data: Dict[str, str]) -> Dict[str, str]:
        """
        Calcula valores derivados a partir dos dados existentes.
        
        Args:
            data: Dicionário com os dados atuais
            
        Returns:
            Dicionário com valores calculados
        """
        derived = {}
        
        # Exemplo: Calcular impedância se temos tensão e corrente
        if data.get("nominalVoltage") and data.get("init_sim_3p"):
            try:
                voltage = float(data["nominalVoltage"])
                current = float(data["init_sim_3p"])
                if current > 0:
                    impedance = voltage / (current * 1.732)  # Impedância trifásica
                    derived["calculated_impedance"] = f"{impedance:.4f}"
            except (ValueError, ZeroDivisionError):
                pass
        
        return derived
    
    @staticmethod
    def get_required_fields() -> List[str]:
        """
        Retorna a lista de campos obrigatórios.
        
        Returns:
            Lista de nomes de campos obrigatórios
        """
        return ["componentType", "nominalVoltage", "nodeBus"]
    
    @staticmethod
    def get_field_tooltip(field_name: str) -> str:
        """
        Retorna um tooltip explicativo para o campo.
        
        Args:
            field_name: Nome do campo
            
        Returns:
            String com o tooltip
        """
        tooltips = {
            "componentType": "Tipo do componente elétrico (Bus, Generator, Load, Transformer)",
            "nominalVoltage": "Tensão nominal do sistema em Volts",
            "asym_halfcycle_3p": "Corrente assimétrica trifásica em meio ciclo (A)",
            "init_sim_3p": "Corrente simétrica RMS inicial trifásica (A)",
            "x-r_3p": "Relação X/R de sequência positiva",
            "nodeBus": "Identificador do nó/barramento",
            "busDescription": "Descrição textual da barra",
        }
        return tooltips.get(field_name, f"Campo: {field_name}")


# Exemplo de uso (não executado, apenas documentação):
if __name__ == "__main__":
    # Este código não será executado em produção, serve apenas como exemplo
    
    model = BarrasModel()
    
    # Obter cabeçalhos
    headers = model.get_column_headers()
    print("Cabeçalhos:", headers)
    
    # Validar dados
    test_data = {
        "componentType": "Bus",
        "nominalVoltage": "13800",
        "nodeBus": "BUS_001",
        "busDescription": "Barramento Principal"
    }
    is_valid, errors = model.validate_data(test_data)
    print(f"Dados válidos: {is_valid}")
    if not is_valid:
        print(f"Erros: {errors}")
    
    # Formatar valor
    formatted = model.format_value("nominalVoltage", "13800")
    print(f"Valor formatado: {formatted}")  # Saída: "13.80 kV"
