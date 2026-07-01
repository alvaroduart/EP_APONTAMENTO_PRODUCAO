from django.urls import path
from producao.presentation import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/ops/', views.list_ops, name='list_ops'),
    path('api/apontamentos/', views.apontamentos, name='apontamentos'),
    path('api/ocorrencias/', views.ocorrencias, name='ocorrencias'),
    path('api/ocorrencias/finalize/', views.finalize_ocorrencia, name='finalize_ocorrencia'),
    path('api/active-state/', views.active_state, name='active_state'),
    path('api/apontamentos/edit/', views.editar_apontamento, name='editar_apontamento'),
    path('api/pcp-metrics/', views.pcp_metrics, name='pcp_metrics'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
