from rest_framework.routers import DefaultRouter
from .views import WorkflowInstanceViewSet

router = DefaultRouter()
router.register(
    "workflow-instances",
    WorkflowInstanceViewSet
)

urlpatterns = router.urls