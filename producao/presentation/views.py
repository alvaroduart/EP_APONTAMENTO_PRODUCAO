import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from producao.infrastructure.repositories import GoogleSheetsProducaoRepository
from producao.application.use_cases import (
    ListarOPsUseCase,
    ApontarProducaoUseCase,
    RegistrarOcorrenciaUseCase,
    EditarApontamentoUseCase
)
from producao.presentation.serializers import validate_fields
from producao.domain.exceptions import BusinessError

def index(request):
    """Renders the main production terminal interface."""
    context = {
        'recursos_json': json.dumps(settings.RECURSOS),
        'motivos_json': json.dumps(settings.MOTIVOS),
    }
    return render(request, 'producao/index.html', context)

def list_ops(request):
    """API endpoint to retrieve the list of active OPs from Google Sheets."""
    try:
        repo = GoogleSheetsProducaoRepository()
        use_case = ListarOPsUseCase(repo)
        ops = use_case.execute()
        
        ops_dict = {}
        for op in ops:
            ops_dict[op.id] = {
                'cliente': op.cliente,
                'produto': op.descricao_produto
            }
        return JsonResponse(ops_dict)
    except FileNotFoundError as e:
        return JsonResponse({'error': 'needs_authentication', 'message': str(e)}, status=401)
    except Exception as e:
        return JsonResponse({'error': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def apontamentos(request):
    """API endpoint to post production appointments to Google Sheets."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        err = validate_fields(data, [
            'op_id', 'cliente', 'descricao_produto', 'data', 'hora', 
            'matricula', 'maquina', 'op_encerrada', 'quantidade'
        ])
        if err:
            return JsonResponse({'error': 'validation_error', 'message': err}, status=400)
            
        repo = GoogleSheetsProducaoRepository()
        use_case = ApontarProducaoUseCase(repo)
        
        apontamento = use_case.execute(
            op_id=str(data['op_id']),
            cliente=str(data['cliente']),
            descricao_produto=str(data['descricao_produto']),
            data=str(data['data']),
            hora=str(data['hora']),
            matricula=str(data['matricula']),
            maquina=str(data['maquina']),
            op_encerrada=bool(data['op_encerrada']),
            quantidade=int(data['quantidade'])
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Apontamento registrado com sucesso no Google Sheets'
        })
    except BusinessError as e:
        return JsonResponse({'error': 'business_error', 'message': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def ocorrencias(request):
    """API endpoint to post occurrences to Google Sheets."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        err = validate_fields(data, [
            'op_id', 'cliente', 'descricao_produto', 'ocorrencia', 
            'data_inicio', 'hora_inicio'
        ])
        if err:
            return JsonResponse({'error': 'validation_error', 'message': err}, status=400)
            
        repo = GoogleSheetsProducaoRepository()
        use_case = RegistrarOcorrenciaUseCase(repo)
        
        use_case.execute(
            op_id=str(data['op_id']),
            cliente=str(data['cliente']),
            descricao_produto=str(data['descricao_produto']),
            ocorrencia=str(data['ocorrencia']),
            data_inicio=str(data['data_inicio']),
            hora_inicio=str(data['hora_inicio']),
            data_fim=data.get('data_fim'),
            hora_fim=data.get('hora_fim')
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Ocorrência registrada com sucesso no Google Sheets'
        })
    except BusinessError as e:
        return JsonResponse({'error': 'business_error', 'message': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def active_state(request):
    """API endpoint to manage active production session state (persistence)."""
    if request.method == 'GET':
        state = request.session.get('active_state', None)
        return JsonResponse({'active_state': state})
        
    elif request.method == 'POST':
        data = json.loads(request.body)
        request.session['active_state'] = data.get('active_state')
        return JsonResponse({'status': 'saved'})
        
    elif request.method == 'DELETE':
        request.session.pop('active_state', None)
        return JsonResponse({'status': 'cleared'})
        
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def editar_apontamento(request):
    """API endpoint to edit an appointment's quantity in Google Sheets."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        err = validate_fields(data, ['filter', 'new_quantidade'])
        if err:
            return JsonResponse({'error': 'validation_error', 'message': err}, status=400)
            
        filter_data = data['filter']
        new_quantidade = int(data['new_quantidade'])
        
        # Verify filter fields are present
        err_filter = validate_fields(filter_data, ['op_id', 'data', 'hora', 'matricula', 'maquina'])
        if err_filter:
            return JsonResponse({'error': 'validation_error', 'message': f"Filter error: {err_filter}"}, status=400)
            
        repo = GoogleSheetsProducaoRepository()
        use_case = EditarApontamentoUseCase(repo)
        success = use_case.execute(filter_data, new_quantidade)
        
        if success:
            return JsonResponse({'status': 'success', 'message': 'Apontamento atualizado com sucesso'})
        else:
            return JsonResponse({'error': 'not_found', 'message': 'Apontamento não encontrado no Google Sheets'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': 'error', 'message': str(e)}, status=500)
