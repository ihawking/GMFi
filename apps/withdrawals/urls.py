from rest_framework.routers import DefaultRouter

from withdrawals.viewsets import WithdrawalViewSet

router = DefaultRouter()
router.register("withdrawal", WithdrawalViewSet)


urlpatterns = router.urls
