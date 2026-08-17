from rest_framework.routers import DefaultRouter

from .views import ApprovalViewSet


router = DefaultRouter()
router.register("approvals", ApprovalViewSet, basename="approval")

urlpatterns = router.urls
