from django.contrib import admin
from .models import Language, TestStage, Recording, ProsodyTestDefinition, TestRun, PreparationPhaseStage, PractiseTestPhaseStage, MainTestPhaseStage, EvaluationPhaseStage
class PractiseTestPhaseStageInline(admin.TabularInline):
    model = PractiseTestPhaseStage
    extra = 1
    ordering = ['order']

class PreparationPhaseStageInline(admin.TabularInline):
    model = PreparationPhaseStage
    extra = 1
    ordering = ['order']


class MainTestPhaseStageInline(admin.TabularInline):
    model = MainTestPhaseStage
    extra = 1
    ordering = ['order']

class EvaluationPhaseStageInline(admin.TabularInline):
    model = EvaluationPhaseStage
    extra = 1
    ordering = ['order']

class ProsodyTestDefinitionAdmin(admin.ModelAdmin):
    inlines = [PreparationPhaseStageInline, PractiseTestPhaseStageInline, MainTestPhaseStageInline, EvaluationPhaseStageInline]

admin.site.register(Language)
admin.site.register(TestStage)
admin.site.register(Recording)
admin.site.register(ProsodyTestDefinition, ProsodyTestDefinitionAdmin)

import csv
from django.http import HttpResponse

def export_testruns_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="testruns.csv"'
    writer = csv.writer(response)
    # List all fields to export
    field_names = [
        'id', 'consent', 'age', 'birth_country', 'grew_up_country', 'other_languages', 'languages_list',
        'education', 'dyslexia', 'asd', 'learning_impairment', 'current_phase', 'current_stage_index',
        'time', 'used_test_definition', 'experiment_trial_index', 'main_trial_order'
    ]
    writer.writerow(field_names)
    for testrun in queryset:
        writer.writerow([
            testrun.id,
            testrun.consent,
            testrun.age,
            testrun.birth_country,
            testrun.grew_up_country,
            testrun.other_languages,
            testrun.languages_list,
            testrun.education,
            testrun.dyslexia,
            testrun.asd,
            testrun.learning_impairment,
            testrun.current_phase,
            testrun.current_stage_index,
            testrun.time,
            str(testrun.used_test_definition) if testrun.used_test_definition else '',
            testrun.experiment_trial_index,
            testrun.main_trial_order
        ])
    return response
export_testruns_csv.short_description = "Export selected testruns as CSV"

class TestRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'current_phase', 'current_stage_index', 'time', 'used_test_definition')
    actions = [export_testruns_csv]

admin.site.register(TestRun, TestRunAdmin)
