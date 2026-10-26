import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse

class ProductionTerminalTests(TestCase):
    def test_index_page(self):
        """Verify that the home page renders correctly with Electro Plastic header."""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Electro Plastic Logo")

    def test_active_state_api(self):
        """Test the Django Session based active state endpoints (GET, POST, DELETE)."""
        # Initial check (should be empty/None)
        response = self.client.get(reverse('active_state'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'active_state': None})

        # Save active state in session
        payload = {'active_state': {'status': 'running', 'active': {'op': '042543', 'recurso': 'MS1000.4'}}}
        response = self.client.post(
            reverse('active_state'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'saved'})

        # Retrieve saved active state
        response = self.client.get(reverse('active_state'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['active_state']['status'], 'running')
        self.assertEqual(response.json()['active_state']['active']['op'], '042543')

        # Clear session active state
        response = self.client.delete(reverse('active_state'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'cleared'})

        # Ensure state is back to None
        response = self.client.get(reverse('active_state'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'active_state': None})

    def test_editar_apontamento_api_with_mock(self):
        """Test editing an appointment via Mocked repository."""
        from unittest.mock import patch
        
        # Patch the repository instance in views.py
        with patch('producao.presentation.views.GoogleSheetsProducaoRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.update_apontamento.return_value = True
            
            payload = {
                'filter': {
                    'op_id': '17711',
                    'data': '26/06/2026',
                    'hora': '08:45:37',
                    'matricula': '123',
                    'maquina': 'MS1000.4'
                },
                'new_quantidade': 150
            }
            
            response = self.client.post(
                reverse('editar_apontamento'),
                data=json.dumps(payload),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'status': 'success', 'message': 'Apontamento atualizado com sucesso'})
            
            # Assert that repository method was called with correct parameters
            mock_repo.update_apontamento.assert_called_once_with(payload['filter'], 150)

    def test_save_apontamento_repository(self):
        """Test that save_apontamento correctly finds next empty row and updates columns A to I."""
        from unittest.mock import MagicMock
        from producao.infrastructure.repositories import GoogleSheetsProducaoRepository
        from producao.domain.entities import Apontamento

        repo = GoogleSheetsProducaoRepository()
        
        # Mock worksheet
        mock_worksheet = MagicMock()
        repo._get_worksheet_by_id = MagicMock(return_value=mock_worksheet)
        
        # col_values(1) returns 5 values (e.g. 5 rows including header)
        mock_worksheet.col_values.return_value = ['OP', '101', '102', '103', '104']
        
        apontamento = Apontamento(
            op_id="12345",
            cliente="Cliente Teste",
            descricao_produto="Produto Teste",
            data="28/06/2026",
            hora="20:00:00",
            matricula="999",
            maquina="M1",
            op_encerrada="Não",
            quantidade=100,
            aparas=0.0
        )
        
        repo.save_apontamento(apontamento)
        
        # It should check col_values of column 1 (A)
        mock_worksheet.col_values.assert_called_once_with(1)
        
        # It should update row 6 (5 existing + 1)
        mock_worksheet.update.assert_called_once_with(
            values=[[
                "12345", "Cliente Teste", "Produto Teste",
                "28/06/2026", "20:00:00", "999", "M1", "Não", 100, 0.0
            ]],
            range_name="A6:J6",
            raw=False
        )

    def test_save_apontamento_with_ocorrencia_apara_col_p(self):
        """Test that save_apontamento with ocorrencia_apara updates A:J and Column P."""
        from unittest.mock import MagicMock, call
        from producao.infrastructure.repositories import GoogleSheetsProducaoRepository
        from producao.domain.entities import Apontamento

        repo = GoogleSheetsProducaoRepository()
        
        mock_worksheet = MagicMock()
        repo._get_worksheet_by_id = MagicMock(return_value=mock_worksheet)
        mock_worksheet.col_values.return_value = ['OP', '101', '102']
        
        apontamento = Apontamento(
            op_id="12345",
            cliente="Cliente Teste",
            descricao_produto="Produto Teste",
            data="28/06/2026",
            hora="20:00:00",
            matricula="999",
            maquina="M1",
            op_encerrada="Não",
            quantidade=100,
            aparas=12.5,
            ocorrencia_apara="Refile"
        )
        
        repo.save_apontamento(apontamento)
        
        mock_worksheet.col_values.assert_called_once_with(1)
        
        # Verify both updates: A4:J4 and P4:P4
        expected_calls = [
            call(
                values=[[
                    "12345", "Cliente Teste", "Produto Teste",
                    "28/06/2026", "20:00:00", "999", "M1", "Não", 100, 12.5
                ]],
                range_name="A4:J4",
                raw=False
            ),
            call(
                values=[["Refile"]],
                range_name="P4:P4",
                raw=False
            )
        ]
        mock_worksheet.update.assert_has_calls(expected_calls)

    def test_apontamentos_api_with_ocorrencia_apara(self):
        """Test posting appointment with ocorrencia_apara through views API."""
        with patch('producao.presentation.views.GoogleSheetsProducaoRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            
            payload = {
                'op_id': '17711',
                'cliente': 'Test Client',
                'descricao_produto': 'Test Prod',
                'data': '26/06/2026',
                'hora': '08:45:37',
                'matricula': '123',
                'maquina': 'MS1000.4',
                'op_encerrada': False,
                'quantidade': 1500,
                'aparas': 8.5,
                'ocorrencia_apara': 'Extrusão'
            }
            
            response = self.client.post(
                reverse('apontamentos'),
                data=json.dumps(payload),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            mock_repo.save_apontamento.assert_called_once()
            saved_apontamento = mock_repo.save_apontamento.call_args[0][0]
            self.assertEqual(saved_apontamento.op_id, '17711')
            self.assertEqual(saved_apontamento.aparas, 8.5)
            self.assertEqual(saved_apontamento.ocorrencia_apara, 'Extrusão')

    def test_apontamentos_api_with_zero_quantidade(self):
        """Test that posting apontamento with quantidade 0 succeeds."""
        from unittest.mock import patch
        
        with patch('producao.presentation.views.GoogleSheetsProducaoRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            
            payload = {
                'op_id': '17711',
                'cliente': 'Test Client',
                'descricao_produto': 'Test Prod',
                'data': '26/06/2026',
                'hora': '08:45:37',
                'matricula': '123',
                'maquina': 'MS1000.4',
                'op_encerrada': False,
                'quantidade': 0,
                'aparas': 0.0,
                'ocorrencia_apara': ''
            }
            
            response = self.client.post(
                reverse('apontamentos'),
                data=json.dumps(payload),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            mock_repo.save_apontamento.assert_called_once()
            saved_apontamento = mock_repo.save_apontamento.call_args[0][0]
            self.assertEqual(saved_apontamento.quantidade, 0)

    def test_admin_dashboard_with_mock(self):
        """Test that the admin dashboard view renders successfully with mocked repository data."""
        from unittest.mock import patch, MagicMock
        
        with patch('producao.presentation.views.GoogleSheetsProducaoRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            # Mock list_apontamentos_raw
            mock_repo.list_apontamentos_raw.return_value = [
                {
                    'op_id': '44579',
                    'cliente': 'INTERBRANDS FOODS LTDA',
                    'descricao_produto': 'SACO PP TRANSP 25.02.000077',
                    'data': '28/06/2026',
                    'hora': '20:02:47',
                    'matricula': '111',
                    'maquina': 'P1307',
                    'op_encerrada': 'Não',
                    'quantidade': '33.000',
                    'hora_hora': '8.000',
                },
                {
                    'op_id': '42115',
                    'cliente': 'AGILBAG CONTAINERS E EMB. FLEXIVEIS LTDA',
                    'descricao_produto': 'MANGA PEBD',
                    'data': '28/06/2026',
                    'hora': '20:03:53',
                    'matricula': '112',
                    'maquina': 'MAQ.01',
                    'op_encerrada': 'Não',
                    'quantidade': '10.000',
                    'hora_hora': '1.000',
                }
            ]
            
            # Mock worksheet for base OPs
            mock_ws_ops = MagicMock()
            mock_ws_ops.get_all_values.return_value = [
                ['NUMERO OP ', 'CODIGO PRODUTO ', 'DESCRIÇÃO PRODUTO ', 'NOME CLIENTE ', 'GRAMA SACO', 'QUANTIDADE OP'],
                ['44579', 'PASCPPLI00155AA', 'SACO PP TRANSP 25.02.000077', 'INTERBRANDS FOODS LTDA', '4,593', '7932.9'],
                ['42115', 'PASCPELI00419AA', 'MANGA PEBD', 'AGILBAG CONTAINERS E EMB. FLEXIVEIS LTDA', '204,4', '2044']
            ]
            
            # Mock worksheet for occurrences
            mock_ws_ocorr = MagicMock()
            mock_ws_ocorr.get_all_values.return_value = [
                ['Ordem Produção', 'Cliente', 'Descrição Produto', 'Ocorrência', 'Data Inicio', 'Hora Inicio', 'Data Fim', 'Hora Fim', 'Maquina'],
                ['44579', 'INTERBRANDS FOODS LTDA', 'SACO PP TRANSP 25.02.000077', 'Banheiro', '28/06/2026', '20:00:00', '', '', 'F75002']
            ]
            
            # Map get_worksheet mock by ID
            def mock_get_worksheet(gid):
                if gid == 1488139834:
                    return mock_ws_ops
                elif gid == 1265473594:
                    return mock_ws_ocorr
                return MagicMock()
                
            mock_repo._get_worksheet_by_id = mock_get_worksheet
            # The class is patched, so its GID constants must be restored for the sheet lookup by id
            mock_repo_class.BASE_OPS_GID = 1488139834
            mock_repo_class.OCORRENCIAS_GID = 1265473594

            response = self.client.get(reverse('admin_dashboard'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Módulo PCP")
            self.assertContains(response, "Solda Lateral")
            self.assertContains(response, "Varejo")
            self.assertContains(response, "Banheiro")

    @patch('producao.presentation.views.datetime')
    def test_machine_status_timeout_ociosa(self, mock_datetime_class):
        """Test that a machine with a pointing older than 1h10 is shown as Ociosa, while one within 1h10 is Operando."""
        from datetime import datetime, timezone, timedelta
        
        tz_brazil = timezone(timedelta(hours=-3))
        
        # Mock datetime.now inside views.py to return a fixed time (12:00 PM)
        fixed_now = datetime(2026, 6, 30, 12, 0, 0, tzinfo=tz_brazil)
        mock_datetime_class.now.return_value = fixed_now
        mock_datetime_class.strptime.side_effect = lambda *args, **kwargs: datetime.strptime(*args, **kwargs)
        
        # Pointing 1: older than 1h10 (e.g. 2 hours ago = 10:00 AM)
        old_time = fixed_now - timedelta(hours=2)
        old_date_str = old_time.strftime("%d/%m/%Y")
        old_hour_str = old_time.strftime("%H:%M:%S")
        
        # Pointing 2: recent (e.g. 30 minutes ago = 11:30 AM)
        recent_time = fixed_now - timedelta(minutes=30)
        recent_date_str = recent_time.strftime("%d/%m/%Y")
        recent_hour_str = recent_time.strftime("%H:%M:%S")
        
        with patch('producao.presentation.views.GoogleSheetsProducaoRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.list_apontamentos_raw.return_value = [
                {
                    'op_id': '111',
                    'cliente': 'Client A',
                    'descricao_produto': 'Prod A',
                    'data': old_date_str,
                    'hora': old_hour_str,
                    'matricula': '101',
                    'maquina': 'MAQ.01',
                    'op_encerrada': 'Não',
                    'quantidade': '100',
                    'hora_hora': '10',
                    'performance_h': '85%',
                    'performance_acm': '80%',
                },
                {
                    'op_id': '222',
                    'cliente': 'Client B',
                    'descricao_produto': 'Prod B',
                    'data': recent_date_str,
                    'hora': recent_hour_str,
                    'matricula': '102',
                    'maquina': 'MAQ.02',
                    'op_encerrada': 'Não',
                    'quantidade': '200',
                    'hora_hora': '20',
                    'performance_h': '95%',
                    'performance_acm': '90%',
                }
            ]
            
            mock_ws_ops = MagicMock()
            mock_ws_ops.get_all_values.return_value = [
                ['NUMERO OP', 'CODIGO PRODUTO', 'DESCRIÇÃO PRODUTO', 'NOME CLIENTE', 'GRAMA SACO', 'QUANTIDADE OP'],
                ['111', 'PASCPPLI00155AA', 'Prod A', 'Client A', '5', '1000'],
                ['222', 'PASCPPLI00155AA', 'Prod B', 'Client B', '6', '2000']
            ]
            
            mock_ws_ocorr = MagicMock()
            mock_ws_ocorr.get_all_values.return_value = [
                ['Ordem Produção', 'Cliente', 'Descrição Produto', 'Ocorrência', 'Data Inicio', 'Hora Inicio', 'Data Fim', 'Hora Fim', 'Maquina']
            ]
            
            def mock_get_worksheet(gid):
                if gid == 1488139834:
                    return mock_ws_ops
                elif gid == 1265473594:
                    return mock_ws_ocorr
                return MagicMock()
                
            mock_repo._get_worksheet_by_id = mock_get_worksheet
            
            response = self.client.get(reverse('admin_dashboard'))
            self.assertEqual(response.status_code, 200)
            
            sections = response.context['sections']
            
            maq01_card = None
            maq02_card = None
            for section in sections:
                for card in section['cards']:
                    if card['code'] == 'MAQ.01':
                        maq01_card = card
                    elif card['code'] == 'MAQ.02':
                        maq02_card = card
            
            self.assertIsNotNone(maq01_card)
            self.assertIsNotNone(maq02_card)
            
            self.assertEqual(maq01_card['status'], 'Ociosa')
            self.assertEqual(maq02_card['status'], 'Operando')

    def test_finalize_ocorrencia_api_success(self):
        """Test finalizing an occurrence with success via mocked repository."""
        from unittest.mock import patch
        
        with patch('producao.presentation.views.GoogleSheetsProducaoRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.finalize_ocorrencia.return_value = True
            
            payload = {
                'op_id': '17711',
                'data_inicio': '26/06/2026',
                'hora_inicio': '08:45:00',
                'data_fim': '26/06/2026',
                'hora_fim': '09:00:00'
            }
            
            response = self.client.post(
                reverse('finalize_ocorrencia'),
                data=json.dumps(payload),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {
                'status': 'success',
                'message': 'Ocorrência finalizada com sucesso no Google Sheets'
            })
            mock_repo.finalize_ocorrencia.assert_called_once_with(
                '17711', '26/06/2026', '08:45:00', '26/06/2026', '09:00:00'
            )

    def test_finalize_ocorrencia_api_not_found(self):
        """Test finalizing a non-existent occurrence yields 404."""
        from unittest.mock import patch
        
        with patch('producao.presentation.views.GoogleSheetsProducaoRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.finalize_ocorrencia.return_value = False
            
            payload = {
                'op_id': '00000',
                'data_inicio': '26/06/2026',
                'hora_inicio': '08:45:00',
                'data_fim': '26/06/2026',
                'hora_fim': '09:00:00'
            }
            
            response = self.client.post(
                reverse('finalize_ocorrencia'),
                data=json.dumps(payload),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {
                'error': 'not_found',
                'message': 'Ocorrência aberta correspondente não encontrada'
            })

    @patch('producao.presentation.views.datetime')
    def test_pcp_metrics_api_success(self, mock_datetime_class):
        """Test fetching PCP metrics for a machine with valid pointing records."""
        from datetime import datetime, timezone, timedelta
        
        tz_brazil = timezone(timedelta(hours=-3))
        fixed_now = datetime(2026, 6, 30, 12, 0, 0, tzinfo=tz_brazil)
        mock_datetime_class.now.return_value = fixed_now
        mock_datetime_class.strptime.side_effect = lambda *args, **kwargs: datetime.strptime(*args, **kwargs)
        
        recent_time = fixed_now - timedelta(minutes=15)
        recent_date_str = recent_time.strftime("%d/%m/%Y")
        recent_hour_str = recent_time.strftime("%H:%M:%S")
        
        with patch('producao.presentation.views.GoogleSheetsProducaoRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.list_apontamentos_raw.return_value = [
                {
                    'op_id': '12345',
                    'cliente': 'Test Client',
                    'descricao_produto': 'Test Product',
                    'data': recent_date_str,
                    'hora': recent_hour_str,
                    'matricula': '456',
                    'maquina': 'MAQ.01',
                    'op_encerrada': 'Não',
                    'quantidade': '500',
                    'hora_hora': '50',
                    'performance_h': '88%',
                    'performance_acm': '92%',
                }
            ]
            
            response = self.client.get(reverse('pcp_metrics'), {'maquina': 'MAQ.01'})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['qtd_produzida'], '50')
            self.assertEqual(data['qtd_acumulada'], '500')
            self.assertEqual(data['qtd_apara'], '0')
            self.assertEqual(data['efficiency'], 88)
            self.assertEqual(data['performance_acumulada'], 92)

    def test_admin_dashboard_with_ocorrencias(self):
        """Test that the admin dashboard view retrieves and formats occurrences successfully."""
        import json
        with patch('producao.presentation.views.GoogleSheetsProducaoRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.list_apontamentos_raw.return_value = []
            
            mock_ws_ops = MagicMock()
            mock_ws_ops.get_all_values.return_value = [
                ['NUMERO OP', 'CODIGO PRODUTO', 'DESCRIÇÃO PRODUTO', 'NOME CLIENTE', 'GRAMA SACO', 'QUANTIDADE OP'],
                ['42574', 'PROD01', 'Saco PEBD', 'Client A', '5', '1000']
            ]
            
            mock_ws_ocorr = MagicMock()
            mock_ws_ocorr.get_all_values.return_value = [
                ['Ordem Produção', 'Cliente', 'Descrição Produto', 'Ocorrência', 'Data Inicio', 'Hora Inicio', 'Data Fim', 'Hora Fim', 'Maquina'],
                ['42574', 'Client A', 'Saco PEBD', 'Ajuste Operacional', '29/06/2026', '11:18:00', '29/06/2026', '11:19:00', 'CS600'],
                ['', '', '', '', '', '', '', '', '']
            ]
            
            def mock_get_worksheet(gid):
                if gid == 1488139834:
                    return mock_ws_ops
                elif gid == 1265473594:
                    return mock_ws_ocorr
                return MagicMock()
                
            mock_repo._get_worksheet_by_id = mock_get_worksheet
            mock_repo_class.BASE_OPS_GID = 1488139834
            mock_repo_class.OCORRENCIAS_GID = 1265473594

            response = self.client.get(reverse('admin_dashboard'))
            self.assertEqual(response.status_code, 200)
            self.assertIn('ocorrencias_json', response.context)
            ocorrencias_data = json.loads(response.context['ocorrencias_json'])
            self.assertEqual(len(ocorrencias_data), 1)
            self.assertEqual(ocorrencias_data[0]['op_id'], '42574')
            self.assertEqual(ocorrencias_data[0]['ocorrencia'], 'Ajuste Operacional')
            self.assertEqual(ocorrencias_data[0]['maquina'], 'CS600')



    def test_parse_ptbr_number(self):
        """Numbers are read as the pt-BR spreadsheet displays them ('.' thousands, ',' decimal)."""
        from producao.presentation.views import parse_ptbr_number
        self.assertEqual(parse_ptbr_number('17.460'), 17460.0)
        self.assertEqual(parse_ptbr_number('22.542,00'), 22542.0)
        self.assertEqual(parse_ptbr_number('59,6'), 59.6)
        # 3 decimal places must not be mistaken for a thousands separator
        self.assertEqual(parse_ptbr_number('0,125'), 0.125)
        self.assertEqual(parse_ptbr_number('6,268'), 6.268)
        for empty in ('', '-', None, 'abc'):
            self.assertEqual(parse_ptbr_number(empty), 0.0)

    def test_build_desempenho_records(self):
        """Raw appointments become slim numeric records credited to the matrícula."""
        from producao.presentation.views import build_desempenho_records
        raw = [
            {'op_id': '45646', 'data': '28/09/2026', 'hora': '08:09:11', 'matricula': '600',
             'hora_hora': '10.977', 'aparas': '0', 'minutos': '62,62', 'novo_padrao': '22.542,00'},
            {'op_id': '45731', 'data': '28/09/2026', 'hora': '13:47:32', 'matricula': '1248',
             'hora_hora': '4.256', 'aparas': '26', 'minutos': '43,25', 'novo_padrao': '8.650,00'},
            # interval without a standard speed ('-'): kept, but esp = 0
            {'op_id': '45716', 'data': '29/09/2026', 'hora': '07:00:15', 'matricula': '600',
             'hora_hora': '4.220', 'aparas': '', 'minutos': '58,78', 'novo_padrao': '-'},
            # discarded: no matrícula / invalid date
            {'op_id': '1', 'data': '28/09/2026', 'hora': '08:00:00', 'matricula': '', 'hora_hora': '1'},
            {'op_id': '1', 'data': '', 'hora': '', 'matricula': '999', 'hora_hora': '1'},
        ]

        records = build_desempenho_records(raw)

        self.assertEqual(len(records), 3)
        self.assertEqual(records[0], {'d': '2026-09-28', 'h': 8, 'mat': '600', 'prod': 10977.0,
                                      'esp': 22542.0, 'min': 62.62, 'kg': 0.0})
        self.assertEqual(records[1]['mat'], '1248')
        self.assertEqual(records[1]['kg'], 26.0)
        self.assertEqual(records[2]['esp'], 0.0)

    def _mock_admin_repo(self, mock_repo_class, apontamentos):
        # The class is patched, so its GID constants must be restored for the sheet lookup by id
        mock_repo_class.BASE_OPS_GID = 1488139834
        mock_repo_class.OCORRENCIAS_GID = 1265473594
        mock_repo = mock_repo_class.return_value
        mock_repo.list_apontamentos_raw.return_value = apontamentos
        mock_ws_ops = MagicMock()
        mock_ws_ops.get_all_values.return_value = [
            ['NUMERO OP', 'CODIGO PRODUTO', 'DESCRIÇÃO PRODUTO', 'NOME CLIENTE', 'GRAMA SACO', 'QUANTIDADE OP'],
            ['45646', 'PROD01', 'Saco', 'Client A', '7,64', '1600'],
        ]
        mock_ws_ocorr = MagicMock()
        mock_ws_ocorr.get_all_values.return_value = [['h'] * 9]

        def mock_get_worksheet(gid):
            if gid == 1488139834:
                return mock_ws_ops
            elif gid == 1265473594:
                return mock_ws_ocorr
            return MagicMock()

        mock_repo._get_worksheet_by_id = mock_get_worksheet

    def test_admin_dashboard_impressao_exposes_desempenho(self):
        """The Impressão dashboard ships the performance tab and its data; Acabamento does not."""
        raw = [{
            'op_id': '45646', 'cliente': 'Client A', 'descricao_produto': 'Saco',
            'data': '28/09/2026', 'hora': '08:09:11', 'matricula': '600', 'maquina': 'FW01',
            'op_encerrada': 'Não', 'quantidade': '17.460', 'aparas': '0', 'hora_hora': '10.977',
            'minutos': '62,62', 'novo_padrao': '22.542,00',
        }]
        with patch('producao.presentation.views.GoogleSheetsProducaoRepository') as mock_repo_class:
            self._mock_admin_repo(mock_repo_class, raw)

            response = self.client.get(reverse('admin_dashboard_impressao'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'data-tab="desempenho"')
            data = json.loads(response.context['desempenho_json'])
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['mat'], '600')
            self.assertEqual(data[0]['prod'], 10977.0)

            response = self.client.get(reverse('admin_dashboard'))
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, 'data-tab="desempenho"')
            self.assertEqual(response.context['desempenho_json'], '[]')

    def test_build_cards_records(self):
        """Card records keep only the sector's machines and use the production day (06:00)."""
        from producao.presentation.views import build_cards_records
        raw = [
            {'maquina': 'FW01', 'data': '30/06/2026', 'hora': '08:00:00', 'hora_hora': '1.200', 'novo_padrao': '1.500,00',
             'aparas': '2,5', 'quantidade': '6.800', 'performance_h': '61%', 'performance_acm': '55%'},
            # madrugada: pertence ao dia de produção anterior
            {'maquina': 'FW01', 'data': '01/07/2026', 'hora': '03:00:00', 'hora_hora': '', 'novo_padrao': '-',
             'aparas': '', 'quantidade': '', 'performance_h': '', 'performance_acm': ''},
            {'maquina': 'OUTRA', 'data': '30/06/2026', 'hora': '08:00:00'},
            {'maquina': 'FW01', 'data': '', 'hora': ''},
        ]
        records = build_cards_records(raw, {'FW01'})
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0], {'m': 'FW01', 'pd': '2026-06-30', 'prod': 1200.0, 'esp': 1500.0, 'kg': 2.5,
                                      'qtd': '6.800', 'pacm': 55, 'ph': 61})
        self.assertEqual(records[1]['pd'], '2026-06-30')
        self.assertEqual((records[1]['qtd'], records[1]['pacm'], records[1]['ph']), ('', None, None))

    def test_sum_aparas_and_format(self):
        """QTD APARA is the sum of every scrap value, shown pt-BR."""
        from producao.presentation.views import sum_aparas, format_ptbr_number
        self.assertEqual(sum_aparas([{'aparas': '0'}, {'aparas': '12,5'}, {'aparas': ''}, {'aparas': '1.000'}]), '1.012,5')
        self.assertEqual(sum_aparas([]), '0')
        self.assertEqual(format_ptbr_number(3.0), '3')
        self.assertEqual(format_ptbr_number(0.126), '0,13')

    @patch('producao.presentation.views.datetime')
    def test_pcp_metrics_qtd_apara_is_day_sum(self, mock_datetime_class):
        """pcp_metrics sums today's scrap for the machine and ignores rows before 06:00."""
        from datetime import datetime, timezone, timedelta
        tz_brazil = timezone(timedelta(hours=-3))
        mock_datetime_class.now.return_value = datetime(2026, 6, 30, 12, 0, 0, tzinfo=tz_brazil)
        mock_datetime_class.strptime.side_effect = lambda *args, **kwargs: datetime.strptime(*args, **kwargs)

        rows = [
            {'maquina': 'MAQ.01', 'data': '30/06/2026', 'hora': '05:59:00', 'aparas': '100'},  # dia anterior
            {'maquina': 'MAQ.01', 'data': '30/06/2026', 'hora': '06:00:00', 'aparas': '0'},
            {'maquina': 'MAQ.01', 'data': '30/06/2026', 'hora': '08:00:00', 'aparas': '2,5'},
            {'maquina': 'MAQ.01', 'data': '30/06/2026', 'hora': '09:00:00', 'aparas': '4'},
            {'maquina': 'MAQ.02', 'data': '30/06/2026', 'hora': '09:00:00', 'aparas': '50'},
        ]
        with patch('producao.presentation.views.GoogleSheetsProducaoRepository') as mock_repo_class:
            mock_repo_class.return_value.list_apontamentos_raw.return_value = rows
            response = self.client.get(reverse('pcp_metrics'), {'maquina': 'MAQ.01'})
            self.assertEqual(response.json()['qtd_apara'], '6,5')

    def _run_apontar(self, existing_rows, data, hora, **kwargs):
        from producao.application.use_cases import ApontarProducaoUseCase
        repo = MagicMock()
        repo.list_apontamentos_raw.return_value = existing_rows
        params = dict(op_id='1', cliente='C', descricao_produto='P', data=data, hora=hora,
                      matricula='600', maquina='FW01', op_encerrada=False, quantidade=0)
        params.update(kwargs)
        return ApontarProducaoUseCase(repo).execute(**params)

    def test_first_apontamento_of_day_is_saved_at_six(self):
        """The machine's first appointment of the production day is stored at 06:00."""
        ap = self._run_apontar([], '30/06/2026', '07:42:10', inicio=True)
        self.assertEqual((ap.data, ap.hora), ('30/06/2026', '06:00:00'))

        # Before 06:00 the production day is still the previous one
        ap = self._run_apontar([], '01/07/2026', '03:15:00')
        self.assertEqual((ap.data, ap.hora), ('30/06/2026', '06:00:00'))

        # Rows of another machine or of the previous day don't count
        previous = [
            {'maquina': 'FW01', 'data': '29/06/2026', 'hora': '23:00:00'},
            {'maquina': 'FW02', 'data': '30/06/2026', 'hora': '06:30:00'},
        ]
        ap = self._run_apontar(previous, '30/06/2026', '07:42:10')
        self.assertEqual(ap.hora, '06:00:00')

    def test_later_apontamentos_keep_real_time(self):
        """Once the machine has a row in the production day, the real time is kept."""
        existing = [{'maquina': 'FW01', 'data': '30/06/2026', 'hora': '06:00:00'}]
        ap = self._run_apontar(existing, '30/06/2026', '08:10:00')
        self.assertEqual((ap.data, ap.hora), ('30/06/2026', '08:10:00'))

    def test_column_h_values(self):
        """Column H: Início / Sim / Turno encerrado / Não (closing the OP wins over closing the shift)."""
        existing = [{'maquina': 'FW01', 'data': '30/06/2026', 'hora': '06:00:00'}]
        cases = [
            ({'inicio': True}, 'Início'),
            ({'op_encerrada': True}, 'Sim'),
            ({'turno_encerrado': True}, 'Turno encerrado'),
            ({'op_encerrada': True, 'turno_encerrado': True}, 'Sim'),
            ({}, 'Não'),
        ]
        for kwargs, expected in cases:
            ap = self._run_apontar(existing, '30/06/2026', '08:10:00', **kwargs)
            self.assertEqual(ap.op_encerrada, expected, kwargs)

    def test_apontamentos_api_turno_encerrado(self):
        """The terminal's 'Encerrar turno' flag reaches column H."""
        with patch('producao.presentation.views.GoogleSheetsProducaoRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            payload = {
                'op_id': '17711', 'cliente': 'C', 'descricao_produto': 'P', 'data': '26/06/2026',
                'hora': '18:00:00', 'matricula': '123', 'maquina': 'MS1000.4', 'op_encerrada': False,
                'turno_encerrado': True, 'quantidade': 10,
            }
            response = self.client.post(reverse('apontamentos'), data=json.dumps(payload), content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(mock_repo.save_apontamento.call_args[0][0].op_encerrada, 'Turno encerrado')
            # No earlier row for the machine that day: saved (and reported back) at 06:00
            self.assertEqual((response.json()['data'], response.json()['hora']), ('26/06/2026', '06:00:00'))

    def test_machine_with_turno_encerrado_is_ociosa(self):
        """A machine whose last row closed the shift shows as Ociosa right away."""
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone(timedelta(hours=-3))) - timedelta(minutes=5)
        raw = [{
            'op_id': '45646', 'cliente': 'Client A', 'descricao_produto': 'Saco',
            'data': now.strftime('%d/%m/%Y'), 'hora': now.strftime('%H:%M:%S'), 'matricula': '600',
            'maquina': 'MAQ.01', 'op_encerrada': 'Turno encerrado', 'quantidade': '10', 'aparas': '3',
        }]
        if now.hour < 6:
            self.skipTest('Row would fall in the previous production day')
        with patch('producao.presentation.views.GoogleSheetsProducaoRepository') as mock_repo_class:
            self._mock_admin_repo(mock_repo_class, raw)
            response = self.client.get(reverse('admin_dashboard'))
            card = next(c for s in response.context['sections'] for c in s['cards'] if c['code'] == 'MAQ.01')
            self.assertEqual(card['status'], 'Ociosa')
            self.assertEqual(card['qtd_apara'], '3')

    def test_save_ocorrencia_writes_matricula_in_column_m(self):
        """The operator's matrícula goes to column M, leaving J:L untouched."""
        from unittest.mock import call
        from producao.infrastructure.repositories import GoogleSheetsProducaoRepository
        from producao.domain.entities import Ocorrencia

        repo = GoogleSheetsProducaoRepository()
        mock_worksheet = MagicMock()
        repo._get_worksheet_by_id = MagicMock(return_value=mock_worksheet)
        mock_worksheet.col_values.return_value = ['OP', '101']

        repo.save_ocorrencia(Ocorrencia(
            op_id='1', cliente='C', descricao_produto='P', ocorrencia='Banheiro',
            data_inicio='30/06/2026', hora_inicio='08:00:00', maquina='FW01', matricula='600'
        ))
        mock_worksheet.update.assert_has_calls([
            call(values=[['1', 'C', 'P', 'Banheiro', '30/06/2026', '08:00:00', '', '', 'FW01']], range_name='A3:I3', raw=False),
            call(values=[['600']], range_name='M3:M3', raw=False),
        ])

    def test_ocorrencias_api_passes_matricula(self):
        with patch('producao.presentation.views.GoogleSheetsProducaoRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            payload = {
                'op_id': '1', 'cliente': 'C', 'descricao_produto': 'P', 'ocorrencia': 'Banheiro',
                'data_inicio': '30/06/2026', 'hora_inicio': '08:00:00', 'maquina': 'FW01', 'matricula': '600',
            }
            response = self.client.post(reverse('ocorrencias'), data=json.dumps(payload), content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(mock_repo.save_ocorrencia.call_args[0][0].matricula, '600')
