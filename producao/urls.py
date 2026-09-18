from django.urls import path
from producao.presentation import views

urlpatterns = [
    # Setor Acabamento (padrão)
    path('', views.index, name='index'),
    path('api/ops/', views.list_ops, name='list_ops'),
    path('api/apontamentos/', views.apontamentos, name='apontamentos'),
    path('api/ocorrencias/', views.ocorrencias, name='ocorrencias'),
    path('api/ocorrencias/finalize/', views.finalize_ocorrencia, name='finalize_ocorrencia'),
    path('api/active-state/', views.active_state, name='active_state'),
    path('api/apontamentos/edit/', views.editar_apontamento, name='editar_apontamento'),
    path('api/pcp-metrics/', views.pcp_metrics, name='pcp_metrics'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Setor Impressão (mesma tela, grava na aba "Impressão" da planilha)
    path('impressao/', views.index, {'setor': 'impressao'}, name='index_impressao'),
    path('impressao/api/ops/', views.list_ops, name='list_ops_impressao'),
    path('impressao/api/apontamentos/', views.apontamentos, {'setor': 'impressao'}, name='apontamentos_impressao'),
    path('impressao/api/ocorrencias/', views.ocorrencias, name='ocorrencias_impressao'),
    path('impressao/api/ocorrencias/finalize/', views.finalize_ocorrencia, name='finalize_ocorrencia_impressao'),
    path('impressao/api/active-state/', views.active_state, {'setor': 'impressao'}, name='active_state_impressao'),
    path('impressao/api/apontamentos/edit/', views.editar_apontamento, {'setor': 'impressao'}, name='editar_apontamento_impressao'),
    path('impressao/api/pcp-metrics/', views.pcp_metrics, {'setor': 'impressao'}, name='pcp_metrics_impressao'),
]
