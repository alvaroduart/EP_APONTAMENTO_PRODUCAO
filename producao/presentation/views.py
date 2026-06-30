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
    EditarApontamentoUseCase,
    FinalizarOcorrenciaUseCase
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
            quantidade=int(data['quantidade']),
            aparas=float(data.get('aparas', 0.0))
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
            'data_inicio', 'hora_inicio', 'maquina'
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
            hora_fim=data.get('hora_fim'),
            maquina=str(data['maquina'])
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
def finalize_ocorrencia(request):
    """API endpoint to finalize an open occurrence in Google Sheets."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        err = validate_fields(data, [
            'op_id', 'data_inicio', 'hora_inicio', 'data_fim', 'hora_fim'
        ])
        if err:
            return JsonResponse({'error': 'validation_error', 'message': err}, status=400)
            
        repo = GoogleSheetsProducaoRepository()
        use_case = FinalizarOcorrenciaUseCase(repo)
        
        success = use_case.execute(
            op_id=str(data['op_id']),
            data_inicio=str(data['data_inicio']),
            hora_inicio=str(data['hora_inicio']),
            data_fim=str(data['data_fim']),
            hora_fim=str(data['hora_fim'])
        )
        
        if success:
            return JsonResponse({
                'status': 'success',
                'message': 'Ocorrência finalizada com sucesso no Google Sheets'
            })
        else:
            return JsonResponse({'error': 'not_found', 'message': 'Ocorrência aberta correspondente não encontrada'}, status=404)
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

def admin_dashboard(request):
    """Renders the administrative dashboard with machine efficiencies."""
    try:
        repo = GoogleSheetsProducaoRepository()
        
        # 1. Fetch pointings and sheets
        apontamentos = repo.list_apontamentos_raw()
        
        # 2. Fetch OPs for grams lookup
        base_ops_sheet = repo._get_worksheet_by_id(1488139834)
        ops_rows = base_ops_sheet.get_all_values()
        op_grams = {}
        for row in ops_rows[1:]:
            if len(row) >= 5:
                op_grams[row[0].strip()] = row[4].strip()
                
        # 3. Fetch occurrences for open occurrence check
        ocorrencias_sheet = repo._get_worksheet_by_id(1265473594)
        ocorrencias_rows = ocorrencias_sheet.get_all_values()
        open_machine_occurrences = {}
        for row in ocorrencias_rows[1:]:
            if len(row) >= 9:
                op_id = row[0].strip()
                data_fim = row[6].strip()
                motive = row[3].strip()
                maquina = row[8].strip()
                if not data_fim and maquina:
                    open_machine_occurrences[maquina] = motive

        # Helper function to clean floats
        def clean_float(val_str):
            if not val_str:
                return 0.0
            try:
                val_clean = val_str.replace(' ', '').strip()
                if ',' in val_clean and '.' in val_clean:
                    val_clean = val_clean.replace('.', '').replace(',', '.')
                elif ',' in val_clean:
                    val_clean = val_clean.replace(',', '.')
                parts = val_clean.split('.')
                if len(parts) == 2 and len(parts[1]) == 3:
                    val_clean = val_clean.replace('.', '')
                return float(val_clean)
            except Exception:
                return 0.0

        # Helper function to clean weight in grams (retains decimal points for small weights)
        def clean_grams(val_str):
            if not val_str:
                return 0.0
            try:
                val_clean = val_str.replace(' ', '').strip()
                val_clean = val_clean.replace(',', '.')
                return float(val_clean)
            except Exception:
                return 0.0


        # Helper function to clean OEE percentage values from Column M
        def clean_oee(val_str):
            if not val_str:
                return 0
            try:
                val_clean = val_str.replace(' ', '').strip()
                is_percent = '%' in val_clean
                val_clean = val_clean.replace('%', '')
                if ',' in val_clean and '.' in val_clean:
                    val_clean = val_clean.replace('.', '').replace(',', '.')
                elif ',' in val_clean:
                    val_clean = val_clean.replace(',', '.')
                parts = val_clean.split('.')
                if len(parts) == 2 and len(parts[1]) == 3:
                    val_clean = val_clean.replace('.', '')
                
                val_num = float(val_clean)
                if val_num <= 1.0 and val_num > 0 and not is_percent:
                    val_num = val_num * 100
                return int(round(val_num))
            except Exception:
                return 0


        # Define categories configuration
        categories_config = {
            'Solda Lateral': ['HS1002', 'HS1001', 'HS1201', 'HS1003', 'MS1004', 'MS1202', 'MS1002', 'MS1003', 'MS1001', 'F75002', 'HSC 70', 'HSC 11', 'SCW700', 'CS600'],
            'Varejo': ['P1301', 'P1302', 'P1303', 'P1304', 'P1305', 'P1306', 'P1307', 'P1308', 'PRV1'],
            'Solda Fundo': ['MAQ.01', 'MAQ.02', 'P1401', 'P1402', 'P1403', 'F75001', 'SM-01']
        }

        sections = []
        for cat_name, mids in categories_config.items():
            cat_cards = []
            for mid in mids:
                pts = [ap for ap in apontamentos if ap['maquina'] == mid]
                
                # Use machine code directly as requested
                display_name = mid
                
                # Determine target speed based on category / specific machine
                target_speed = 100.0
                if cat_name == 'Varejo':
                    target_speed = 200.0
                elif cat_name == 'Solda Lateral':
                    target_speed = 100.0
                elif cat_name == 'Solda Fundo':
                    target_speed = 200.0
                
                # Specific overrides
                if mid == 'MAQ.01': target_speed = 284.0
                elif mid == 'MAQ.02': target_speed = 250.0
                elif mid == 'P1307': target_speed = 45.0
                elif mid == 'F75001': target_speed = 200.0
                elif mid == 'F75002': target_speed = 214.0
                elif mid == 'HS1001': target_speed = 99.0

                if mid in open_machine_occurrences:
                    status = open_machine_occurrences[mid]
                    status_class = 'manutencao'
                else:
                    if pts:
                        latest = pts[-1]
                        op_encerrada = latest['op_encerrada']
                        if op_encerrada == 'Sim':
                            status = 'Ociosa'
                            status_class = 'ociosa'
                        else:
                            status = 'Operando'
                            status_class = 'operando'
                    else:
                        status = 'Ociosa'
                        status_class = 'ociosa'

                if pts:
                    latest = pts[-1]
                    qtd_produzida = latest.get('hora_hora', '—')
                    qtd_acumulada = latest.get('quantidade', '—')
                    cliente = latest.get('cliente', '')
                    
                    eff = 0
                    for ap in reversed(pts):
                        oee_val = ap.get('oee_eficiencia', '').strip()
                        if oee_val:
                            eff = clean_oee(oee_val)
                            break

                    perf_acumulada = 0
                    for ap in reversed(pts):
                        perf_val = ap.get('performance_acumulada_raw', '').strip()
                        if perf_val:
                            perf_acumulada = clean_oee(perf_val)
                            break
                            
                    is_live = True
                else:
                    qtd_produzida = '—'
                    qtd_acumulada = '—'
                    cliente = '—'
                    eff = 0
                    perf_acumulada = 0
                    is_live = False

                cat_cards.append({
                    'code': mid,
                    'name': display_name,
                    'status': status,
                    'status_class': status_class,
                    'qtd_produzida': qtd_produzida,
                    'qtd_acumulada': qtd_acumulada,
                    'performance_acumulada': perf_acumulada,
                    'efficiency': eff,
                    'cliente': cliente,
                    'is_live': is_live
                })
            sections.append({
                'name': cat_name,
                'cards': cat_cards
            })

        context = {
            'sections': sections
        }
        return render(request, 'producao/admin_dashboard.html', context)
    except FileNotFoundError as e:
        return render(request, 'producao/admin_dashboard.html', {'error': 'needs_authentication', 'message': str(e)})
    except Exception as e:
        return render(request, 'producao/admin_dashboard.html', {'error': 'error', 'message': str(e)})
