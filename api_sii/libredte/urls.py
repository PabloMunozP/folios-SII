from django.urls import path
from .views import PedirFolios

urlpatterns = [
    path('solicitarFoliosDTE/',PedirFolios.as_view(),name='api_getFolios'),
    # path('deleteFolios/',AnularFolios.as_view(), name='api_deleteFolios' ),
    # path('consultaFolios/',ConsultarFolio.as_view(),name='api_consultaFolios'),
    # path('logsDTE/', ViewLog.as_view(),name='logs')
]