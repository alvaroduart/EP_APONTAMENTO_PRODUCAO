from typing import List, Optional
from producao.domain.entities import OP, Apontamento, Ocorrencia
from producao.application.interfaces import IProducaoRepository
from producao.infrastructure.google_sheets import get_spreadsheet

class GoogleSheetsProducaoRepository(IProducaoRepository):
    def __init__(self):
        self._spreadsheet = None

    @property
    def spreadsheet(self):
        if self._spreadsheet is None:
            self._spreadsheet = get_spreadsheet()
        return self._spreadsheet

    def _get_worksheet_by_id(self, gid: int):
        for ws in self.spreadsheet.worksheets():
            if str(ws.id) == str(gid):
                return ws
        # Fallback to the first sheet if not found
        return self.spreadsheet.get_worksheet(0)

    def list_ops(self) -> List[OP]:
        # Aba 3: Base OPs (gid = 1488139834)
        sheet = self._get_worksheet_by_id(1488139834)
        rows = sheet.get_all_values()
        
        ops = []
        if not rows:
            return ops

        # Parse header to find column indices dynamically
        header = [col.strip().lower() for col in rows[0]]
        op_idx = 0
        cliente_idx = 1
        desc_idx = 2

        for i, name in enumerate(header):
            # Check for OP number, avoiding quantity columns
            if ("ordem" in name or "op" in name) and "quant" not in name:
                op_idx = i
            elif "cliente" in name:
                cliente_idx = i
            # Check for product description, avoiding product code/id columns
            elif ("produto" in name or "descri" in name) and "cod" not in name:
                desc_idx = i

        for row in rows[1:]:
            if len(row) > max(op_idx, cliente_idx, desc_idx):
                op_id = row[op_idx].strip()
                if op_id:  # Skip empty OP entries
                    ops.append(OP(
                        id=op_id,
                        cliente=row[cliente_idx].strip(),
                        descricao_produto=row[desc_idx].strip()
                    ))
        return ops

    def get_op(self, op_id: str) -> Optional[OP]:
        for op in self.list_ops():
            if op.id == op_id:
                return op
        return None

    def save_apontamento(self, apontamento: Apontamento) -> None:
        # Aba 1: Apontamentos (gid = 0)
        sheet = self._get_worksheet_by_id(0)
        
        # Obter os valores da coluna A para encontrar a próxima linha vazia
        col_a_values = sheet.col_values(1)
        next_row = len(col_a_values) + 1
        
        # Limitar a atualização estritamente até a coluna I (A:I)
        # para evitar sobrescrever fórmulas pessoais nas colunas seguintes (J, K...)
        values = [
            apontamento.op_id,
            apontamento.cliente,
            apontamento.descricao_produto,
            apontamento.data,
            apontamento.hora,
            apontamento.matricula,
            apontamento.maquina,
            apontamento.op_encerrada,
            apontamento.quantidade
        ]
        
        sheet.update(
            values=[values],
            range_name=f"A{next_row}:I{next_row}",
            raw=False
        )

    def save_ocorrencia(self, ocorrencia: Ocorrencia) -> None:
        # Aba 2: Ocorrencias (gid = 1265473594)
        sheet = self._get_worksheet_by_id(1265473594)
        sheet.append_row([
            ocorrencia.op_id,
            ocorrencia.cliente,
            ocorrencia.descricao_produto,
            ocorrencia.ocorrencia,
            ocorrencia.data_inicio,
            ocorrencia.hora_inicio,
            ocorrencia.data_fim or "",
            ocorrencia.hora_fim or ""
        ])

    def update_apontamento(self, filter_data: dict, new_quantidade: int) -> bool:
        # Aba 1: Apontamentos (gid = 0)
        sheet = self._get_worksheet_by_id(0)
        rows = sheet.get_all_values()
        
        if not rows:
            return False
            
        for idx, row in enumerate(rows[1:], start=2):
            if (len(row) >= 9 and
                row[0].strip() == str(filter_data['op_id']).strip() and
                row[3].strip() == str(filter_data['data']).strip() and
                row[4].strip() == str(filter_data['hora']).strip() and
                row[5].strip() == str(filter_data['matricula']).strip() and
                row[6].strip() == str(filter_data['maquina']).strip()):
                
                # Update Quantity (Col 9 in 1-based index)
                sheet.update_cell(idx, 9, new_quantidade)
                return True
                
        return False
