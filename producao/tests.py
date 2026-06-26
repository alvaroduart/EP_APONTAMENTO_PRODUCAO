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
