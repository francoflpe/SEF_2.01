import json
import os
from typing import Any, Dict, Optional

_DEFAULT_MAP = {
    "version": 1,
    "types": {
        "barras": {
            "componentType": { "nomeExcel": "ComponentType" },
            "nominalVoltage": { "nomeExcel": "SystemNominalVoltage (V)" },
            "asym_halfcycle_3p": { "nomeExcel": "Asym3P 1/2 Cycle (A)" },
            "init_sim_3p": { "nomeExcel": "InitSymRMS 3P (A)" },
            "x-r_3p": { "nomeExcel": "X/R Pos" },
            "asym_halfcycle_slg": { "nomeExcel": "AsymSLG 1/2 Cycle (A)" },
            "init_sim_slg": { "nomeExcel": "InitSymRMS SLG (A)" },
            "x-r_slg": { "nomeExcel": "X/R SLG (pu)" },
            "nodeBus": { "nomeExcel": "NodeBus" },
            "busDescription": { "nomeExcel": "Description" },
            "iec909_ikpp_3p": { "nomeExcel": "IEC909 Ikpp 3P (kA)" },
            "iec909_ikpp_slg": { "nomeExcel": "IEC909 Ikpp SLG (kA)" },
            "iec909_ip_3p": { "nomeExcel": "IEC909 Ip 3P (kA)" },
            "iec909_ip_slg": { "nomeExcel": "IEC909 Ip SLG (kA)" },
            "iec909_ib_sim_3p": { "nomeExcel": "IEC909 Ib Sym 3P (kA)" },
            "iec909_ib_sim_slg": { "nomeExcel": "IEC909 Ib Sym SLG (kA)" },
            "iec909_ik_3p": { "nomeExcel": "IEC909 Ik 3P (kA)" },
            "iec909_ik_slg": { "nomeExcel": "IEC909 Ik SLG (kA)" },
            "iec909_ib_assim_3p": { "nomeExcel": "IEC909 Ib Asym 3P (kA)" },
            "iec909_ib_assim_slg": { "nomeExcel": "IEC909 Ib Asym SLG (kA)" },
            "iec909_idc_3p": { "nomeExcel": "IEC909 Idc 3P (kA)" },
            "iec909_idc_slg": { "nomeExcel": "IEC909 Idc SLG (kA)" },
            "iec909_tmin": { "nomeExcel": "IEC909 Tmin (s)" },
            "asym_attime_3p": { "nomeExcel": "AsymFaultCurrentAtTime 3P (A)" },
            "continuosRating": { "nomeExcel": "ContinuousRating (A)" },
            "seriesRating": { "nomeExcel": "SeriesRating (kA)" },
            "shortCircuitRating": { "nomeExcel": "ShortCircuitRating (kA)" },
            "inService": { "nomeExcel": "InService" },
            "energizeState": { "nomeExcel": "Energize State" }
        },
        "cabos_bt": {
            "componentType": { "nomeExcel": "ComponentType" },
            "qtdPerPhase": { "nomeExcel": "QtyPerPhase" },
            "cableSize": { "nomeExcel": "CableSize (mm2)" },
            "conducDesc": { "nomeExcel": "Conductor Desc" },
            "ConducType": { "nomeExcel": "ConductorType" },
            "InsulClass": { "nomeExcel": "InsulationClass" },
            "InsulType": { "nomeExcel": "InsulationType" },
            "installation": { "nomeExcel": "Installation" },
            "ampDesc": { "nomeExcel": "AmpacityDescription" },
            "ampacity": { "nomeExcel": "Ampacity (A)" },
            "connectedComponent1": { "nomeExcel": "ConnectedComponent1" },
            "connectedComponent2": { "nomeExcel": "ConnectedComponent2" },
            "tempContinous": { "nomeExcel": "Temperature Continuous (C)" },
            "tempDamage": { "nomeExcel": "Temperature Damage (C)" },
            "connectedBus": { "nomeExcel": "ConnectedBus" },
            "asym_attime_3p": { "nomeExcel": "AsymFaultCurrentAtTime 3P (A)" },
            "connectedBus2": { "nomeExcel": "ConnectedBus2" },
            "asym_attime_3p_bus2": { "nomeExcel": "AsymFaultCurrentAtTime 3P Bus2 (A)" },
            "tempAmbient": { "nomeExcel": "Temperature Ambient (C)" },
            "init_sim_3p": { "nomeExcel": "InitSymRMS 3P (A)" },
            "init_sim_3p_bus2": { "nomeExcel": "InitSymRMS 3P Bus2 (A)" },
            "inService": { "nomeExcel": "InService" },
            "energizeState": { "nomeExcel": "Energize State" },
            "asym_attime_slg": { "nomeExcel": "AsymFaultCurrentAtTime SLG (A)" },
            "asym_attime_slg_bus2": { "nomeExcel": "AsymFaultCurrentAtTime SLG Bus2 (A)" },
            "init_sim_slg": { "nomeExcel": "InitSymRMS SLG (A)" },
            "init_sim_slg_bus2": { "nomeExcel": "InitSymRMS SLG Bus2 (A)" }
        },
        "cabos_mt": {
            "componentType": { "nomeExcel": "ComponentType" },
            "qtdPerPhase": { "nomeExcel": "QtyPerPhase" },
            "cableSize": { "nomeExcel": "CableSize (mm2)" },
            "conducDesc": { "nomeExcel": "Conductor Desc" },
            "ConducType": { "nomeExcel": "ConductorType" },
            "InsulClass": { "nomeExcel": "InsulationClass" },
            "InsulType": { "nomeExcel": "InsulationType" },
            "installation": { "nomeExcel": "Installation" },
            "ampDesc": { "nomeExcel": "AmpacityDescription" },
            "ampacity": { "nomeExcel": "Ampacity (A)" },
            "connectedComponent1": { "nomeExcel": "ConnectedComponent1" },
            "connectedComponent2": { "nomeExcel": "ConnectedComponent2" },
            "tempContinous": { "nomeExcel": "Temperature Continuous (C)" },
            "tempDamage": { "nomeExcel": "Temperature Damage (C)" },
            "connectedBus": { "nomeExcel": "ConnectedBus" },
            "asym_attime_3p": { "nomeExcel": "AsymFaultCurrentAtTime 3P (A)" },
            "connectedBus2": { "nomeExcel": "ConnectedBus2" },
            "asym_attime_3p_bus2": { "nomeExcel": "AsymFaultCurrentAtTime 3P Bus2 (A)" },
            "tempAmbient": { "nomeExcel": "Temperature Ambient (C)" },
            "init_sim_3p": { "nomeExcel": "InitSymRMS 3P (A)" },
            "init_sim_3p_bus2": { "nomeExcel": "InitSymRMS 3P Bus2 (A)" },
            "inService": { "nomeExcel": "InService" },
            "energizeState": { "nomeExcel": "Energize State" },
            "asym_attime_slg": { "nomeExcel": "AsymFaultCurrentAtTime SLG (A)" },
            "asym_attime_slg_bus2": { "nomeExcel": "AsymFaultCurrentAtTime SLG Bus2 (A)" },
            "init_sim_slg": { "nomeExcel": "InitSymRMS SLG (A)" },
            "init_sim_slg_bus2": { "nomeExcel": "InitSymRMS SLG Bus2 (A)" }
        }
    }
}

_cache: Optional[Dict[str, Any]] = None

_TYPE_TO_LABEL_MAP = None

def _get_type_to_label_map() -> Dict[str, str]:
    """Carrega e cacheia o mapa de `dataType` para `displayName`."""
    global _TYPE_TO_LABEL_MAP
    if _TYPE_TO_LABEL_MAP is None:
        _TYPE_TO_LABEL_MAP = {
            "barras": "Barras",
            "disj_bt": "Disjuntores BT",
            "disj_mt": "Disjuntores MT",
            "fusiveis": "Fusíveis",
            "chaves_sec": "Chaves Seccionadoras",
            "cabos_bt": "Cabos BT",
            "cabos_mt": "Cabos MT",
            "saturacao_tc": "Saturação TC",
        }
    return _TYPE_TO_LABEL_MAP

def get_label(type_name: str) -> Optional[str]:
    """Retorna o nome de exibição (label) para um `dataType`."""
    return _get_type_to_label_map().get(type_name)

def _default_path() -> str:
    return os.path.join(os.path.dirname(__file__), "data_map.json")


def load_map(path: Optional[str] = None) -> Dict[str, Any]:
    """Carrega o mapa de dados do arquivo JSON. Se não existir, cria com o default."""
    global _cache
    if _cache is not None:
        return _cache

    p = path if path else _default_path()
    # If the file does not exist, do not create a default file here.
    # Higher-level code should create or provide a data_map.json when needed.
    if not os.path.exists(p):
        _cache = {}
        return _cache

    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            _cache = data
            return data
    except Exception:
        # If the file exists but cannot be read/parsed, return an empty map.
        _cache = {}
        return _cache


def save_map(map_dict: Dict[str, Any], path: Optional[str] = None) -> bool:
    p = path if path else _default_path()
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(map_dict, f, indent=4, ensure_ascii=False)
        global _cache
        _cache = map_dict
        return True
    except Exception:
        return False


def get_schema(type_name: str) -> Any:
    """Retorna o schema para o tipo solicitado.

    Comportamento alterado:
    - Se o arquivo `data_map.json` não existir ou não puder ser lido, retorna `True`.
    - Se o arquivo existir, mas o tipo não for encontrado, retorna um dicionário vazio.
    - Se o tipo existir, retorna uma cópia do dicionário do schema.
    """
    p = _default_path()
    # If the data_map file is missing, indicate by returning True
    if not os.path.exists(p):
        return True

    mp = load_map()
    if not mp:
        # load_map failed to read/parse the map -> signal with True
        return True

    types = mp.get("types", {})
    schema = types.get(type_name)
    if schema is None:
        return {}
    return schema.copy() if isinstance(schema, dict) else schema
