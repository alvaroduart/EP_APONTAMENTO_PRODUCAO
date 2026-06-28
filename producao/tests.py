import json
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
            quantidade=100
        )
        
        repo.save_apontamento(apontamento)
        
        # It should check col_values of column 1 (A)
        mock_worksheet.col_values.assert_called_once_with(1)
        
        # It should update row 6 (5 existing + 1)
        mock_worksheet.update.assert_called_once_with(
            values=[[
                "12345", "Cliente Teste", "Produto Teste",
                "28/06/2026", "20:00:00", "999", "M1", "Não", 100
            ]],
            range_name="A6:I6",
            raw=False
        )
