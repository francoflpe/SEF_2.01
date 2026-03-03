# ====================================================================
# DATA MODELS - Modelos Específicos por Tipo de Dado
# ====================================================================
"""
Este pacote contém módulos específicos para cada tipo de dado (dataType).

Estrutura planejada:
    - barras_model.py: Lógica específica para dados de "barras"
    - cabos_bt_model.py: Lógica específica para dados de "cabos_bt"
    - cabos_mt_model.py: Lógica específica para dados de "cabos_mt"
    - disj_bt_model.py: Lógica específica para dados de "disj_bt"
    - disj_mt_model.py: Lógica específica para dados de "disj_mt"
    - fusiveis_model.py: Lógica específica para dados de "fusiveis"
    - chaves_sec_model.py: Lógica específica para dados de "chaves_sec"
    - saturacao_tc_model.py: Lógica específica para dados de "saturacao_tc"

Cada módulo poderá conter:
    - Validações específicas do tipo de dado
    - Cabeçalhos de tabela customizados
    - Lógica de cálculo/conversão
    - Formatação de exibição
    - Widgets de edição especializados

Exemplo de uso futuro:
    from data_models.barras_model import BarrasModel
    
    barras = BarrasModel()
    headers = barras.get_column_headers()
    is_valid = barras.validate_data(data_dict)
"""

# Placeholder para importações futuras
# from .barras_model import BarrasModel
# from .cabos_bt_model import CabosBTModel
# ...

__all__ = []  # Será populado conforme os módulos forem criados
