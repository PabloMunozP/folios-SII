from django.urls import path
from .views import PedirFolios,AnularFolios,ConsultarFolio,ViewLog


urlpatterns = [
    path('solicitarFolios/',PedirFolios.as_view(),name='api_getFolios'),
    path('anularFolios/',AnularFolios.as_view(), name='api_deleteFolios' ),
    path('consultarFolios/',ConsultarFolio.as_view(),name='api_consultaFolios'),
    path('logs/', ViewLog.as_view(),name='logs')
]