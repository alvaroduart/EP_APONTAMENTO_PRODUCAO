from dataclasses import dataclass
from typing import Optional

@dataclass
class OP:
    id: str
    cliente: str
    descricao_produto: str

@dataclass
class Ocorrencia:
    op_id: str
    cliente: str
    descricao_produto: str
    ocorrencia: str
    data_inicio: str  # DD/MM/YYYY
    hora_inicio: str  # HH:MM:SS
    data_fim: Optional[str] = None  # DD/MM/YYYY
    hora_fim: Optional[str] = None  # HH:MM:SS
    maquina: Optional[str] = None

@dataclass
class Apontamento:
    op_id: str
    cliente: str
    descricao_produto: str
    data: str  # DD/MM/YYYY
    hora: str  # HH:MM:SS
    matricula: str
    maquina: str
    op_encerrada: str  # "Sim" or "Não"
    quantidade: int
    aparas: float = 0.0
