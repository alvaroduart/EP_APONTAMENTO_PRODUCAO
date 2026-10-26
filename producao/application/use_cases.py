from datetime import datetime, timedelta
from typing import List, Optional
from producao.domain.entities import OP, Apontamento, Ocorrencia
from producao.domain.exceptions import OPNotFoundError
from producao.application.interfaces import IProducaoRepository

# O dia de produção começa às 06:00 (apontamentos da madrugada pertencem ao dia anterior)
HORA_INICIO_DIA_PRODUCAO = 6
FORMATO_DATA_HORA = "%d/%m/%Y %H:%M:%S"

def inicio_dia_producao(momento: datetime) -> datetime:
    inicio = momento.replace(hour=HORA_INICIO_DIA_PRODUCAO, minute=0, second=0, microsecond=0)
    return inicio if momento >= inicio else inicio - timedelta(days=1)

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
        quantidade: int,
        aparas: float = 0.0,
        ocorrencia_apara: str = "",
        inicio: bool = False,
        turno_encerrado: bool = False
    ) -> Apontamento:
        if inicio:
            op_encerrada_str = "Início"
        elif op_encerrada:
            op_encerrada_str = "Sim"
        elif turno_encerrado:
            op_encerrada_str = "Turno encerrado"
        else:
            op_encerrada_str = "Não"
        data, hora = self._primeiro_do_dia_as_seis(maquina, data, hora)
        apontamento = Apontamento(
            op_id=op_id,
            cliente=cliente,
            descricao_produto=descricao_produto,
            data=data,
            hora=hora,
            matricula=matricula,
            maquina=maquina,
            op_encerrada=op_encerrada_str,
            quantidade=quantidade,
            aparas=aparas,
            ocorrencia_apara=ocorrencia_apara
        )
        self.repo.save_apontamento(apontamento)
        return apontamento

    def _primeiro_do_dia_as_seis(self, maquina: str, data: str, hora: str):
        """O 1º apontamento da máquina no dia de produção é gravado às 06:00, seja qual for a hora real."""
        try:
            momento = datetime.strptime(f"{data} {hora}", FORMATO_DATA_HORA)
        except ValueError:
            return data, hora
        inicio = inicio_dia_producao(momento)
        for ap in self.repo.list_apontamentos_raw():
            if ap.get('maquina', '').strip() != maquina:
                continue
            try:
                dt = datetime.strptime(f"{ap.get('data', '').strip()} {ap.get('hora', '').strip()}", FORMATO_DATA_HORA)
            except ValueError:
                continue
            if dt >= inicio:
                return data, hora
        return inicio.strftime("%d/%m/%Y"), inicio.strftime("%H:%M:%S")

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
        hora_fim: Optional[str] = None,
        maquina: Optional[str] = None,
        matricula: Optional[str] = None
    ) -> Ocorrencia:
        entry = Ocorrencia(
            op_id=op_id,
            cliente=cliente,
            descricao_produto=descricao_produto,
            ocorrencia=ocorrencia,
            data_inicio=data_inicio,
            hora_inicio=hora_inicio,
            data_fim=data_fim,
            hora_fim=hora_fim,
            maquina=maquina,
            matricula=matricula
        )
        self.repo.save_ocorrencia(entry)
        return entry

class EditarApontamentoUseCase:
    def __init__(self, repo: IProducaoRepository):
        self.repo = repo

    def execute(self, filter_data: dict, new_quantidade: int) -> bool:
        return self.repo.update_apontamento(filter_data, new_quantidade)

class FinalizarOcorrenciaUseCase:
    def __init__(self, repo: IProducaoRepository):
        self.repo = repo

    def execute(self, op_id: str, data_inicio: str, hora_inicio: str, data_fim: str, hora_fim: str) -> bool:
        return self.repo.finalize_ocorrencia(op_id, data_inicio, hora_inicio, data_fim, hora_fim)
