from django.contrib import admin

from .models import (
    WorkflowTemplate,
    WorkflowStep,
)

admin.site.register(WorkflowTemplate)
admin.site.register(WorkflowStep)