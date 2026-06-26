from typing import List, Optional
from producao.domain.entities import OP, Apontamento, Ocorrencia
from producao.domain.exceptions import OPNotFoundError
from producao.application.interfaces import IProducaoRepository

class ListarOPsUseCase:
    def __init__(self, repo: IProducaoRepository):
        self.repo = repo

    def execute(self) -> List[OP]:
        return self.repo.list_ops()

class ObterOPUseCase:
    def __init__(self, repo: IProducaoRepository):
        self.repo = repo

    def execute(self, op_id: str) -> OP:
        op = self.repo.get_op(op_id)
        if not op:
            raise OPNotFoundError(f"Ordem de Produção {op_id} não encontrada.")
        return op

class ApontarProducaoUseCase:
    def __init__(self, repo: IProducaoRepository):
        self.repo = repo

    def execute(
        self,
        op_id: str,
        cliente: str,
        descricao_produto: str,
        data: str,
        hora: str,
        matricula: str,
        maquina: str,
        op_encerrada: bool,
        quantidade: int
    ) -> Apontamento:
        op_encerrada_str = "Sim" if op_encerrada else "Não"
        apontamento = Apontamento(
            op_id=op_id,
            cliente=cliente,
            descricao_produto=descricao_produto,
            data=data,
            hora=hora,
            matricula=matricula,
            maquina=maquina,
            op_encerrada=op_encerrada_str,
            quantidade=quantidade
        )
        self.repo.save_apontamento(apontamento)
        return apontamento

class RegistrarOcorrenciaUseCase:
    def __init__(self, repo: IProducaoRepository):
        self.repo = repo

    def execute(
        self,
        op_id: str,
        cliente: str,
        descricao_produto: str,
        ocorrencia: str,
        data_inicio: str,
        hora_inicio: str,
        data_fim: Optional[str] = None,
        hora_fim: Optional[str] = None
    ) -> Ocorrencia:
        entry = Ocorrencia(
            op_id=op_id,
            cliente=cliente,
            descricao_produto=descricao_produto,
            ocorrencia=ocorrencia,
            data_inicio=data_inicio,
            hora_inicio=hora_inicio,
            data_fim=data_fim,
            hora_fim=hora_fim
        )
        self.repo.save_ocorrencia(entry)
        return entry

class EditarApontamentoUseCase:
    def __init__(self, repo: IProducaoRepository):
        self.repo = repo

    def execute(self, filter_data: dict, new_quantidade: int) -> bool:
        return self.repo.update_apontamento(filter_data, new_quantidade)
