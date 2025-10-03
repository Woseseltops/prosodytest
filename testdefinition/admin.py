from django.contrib import admin
from .models import Language, TestStage, Recording, ProsodyTestDefinition, TestRun, PreparationPhaseStage, ExperimentPhaseStage, EvaluationPhaseStage

class PreparationPhaseStageInline(admin.TabularInline):
    model = PreparationPhaseStage
    extra = 1
    ordering = ['order']

class ExperimentPhaseStageInline(admin.TabularInline):
    model = ExperimentPhaseStage
    extra = 1
    ordering = ['order']

class EvaluationPhaseStageInline(admin.TabularInline):
    model = EvaluationPhaseStage
    extra = 1
    ordering = ['order']

class ProsodyTestDefinitionAdmin(admin.ModelAdmin):
    inlines = [PreparationPhaseStageInline, ExperimentPhaseStageInline, EvaluationPhaseStageInline]

admin.site.register(Language)
admin.site.register(TestStage)
admin.site.register(Recording)
admin.site.register(ProsodyTestDefinition, ProsodyTestDefinitionAdmin)
class TestRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'participant_name', 'current_phase', 'current_stage_index', 'time', 'used_test_definition')

admin.site.register(TestRun, TestRunAdmin)
