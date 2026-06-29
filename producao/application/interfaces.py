from abc import ABC, abstractmethod
from typing import List, Optional
from producao.domain.entities import OP, Apontamento, Ocorrencia

class IProducaoRepository(ABC):
    @abstractmethod
    def list_ops(self) -> List[OP]:
        """Fetch all available production orders."""
        pass

    @abstractmethod
    def get_op(self, op_id: str) -> Optional[OP]:
        """Fetch details of a single production order by ID."""
        pass

    @abstractmethod
    def save_apontamento(self, apontamento: Apontamento) -> None:
        """Register a new production appointment."""
        pass

    @abstractmethod
    def save_ocorrencia(self, ocorrencia: Ocorrencia) -> None:
        """Register a new occurrence."""
        pass

    @abstractmethod
    def update_apontamento(self, filter_data: dict, new_quantidade: int) -> bool:
        """Update an existing appointment's quantity in repository."""
        pass

    @abstractmethod
    def finalize_ocorrencia(self, op_id: str, data_inicio: str, hora_inicio: str, data_fim: str, hora_fim: str) -> bool:
        """Finalize an existing open occurrence by updating its end date and time."""
        pass
