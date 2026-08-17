from rest_framework.routers import DefaultRouter

from .views import WorkflowStepViewSet, WorkflowTemplateViewSet


router = DefaultRouter()
router.register("workflows", WorkflowTemplateViewSet, basename="workflow")
router.register("workflow-steps", WorkflowStepViewSet, basename="workflow-step")

urlpatterns = router.urls
