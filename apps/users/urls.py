from django.urls import path
from users.views import DepositAddress

urlpatterns = [
    path("deposit-address/", DepositAddress.as_view(), name="get_deposit_address"),
]
