
from django.shortcuts import render
from .models import ProsodyTestDefinition, PreparationPhaseStage

from .models import ProsodyTestDefinition, PreparationPhaseStage, TestRun




from .models import ExperimentPhaseStage, EvaluationPhaseStage

def get_all_stages_for_phase(test_def, phase):

    if phase == 'preparation':
        return list(PreparationPhaseStage.objects.filter(prosody_test=test_def).order_by('order'))
    elif phase == 'experiment':
        return list(ExperimentPhaseStage.objects.filter(prosody_test=test_def).order_by('order'))
    elif phase == 'evaluation':
        return list(EvaluationPhaseStage.objects.filter(prosody_test=test_def).order_by('order'))
    return []

def stage(request):
    
    test_def = ProsodyTestDefinition.objects.first()
    stage_obj = None
    template_name = 'testdefinition/default.html'

    if not test_def:
        return render(request, 'testdefinition/no_test_definition.html')

    # Prefer run id from GET parameters, else session, else start new
    testrun_id = request.GET.get('run')
    testrun = None
    
    if not testrun_id:
        testrun = TestRun.objects.create(
            consent=False,
            participant_name="Anonymous",
            current_phase='preparation',
            current_stage_index=0,
            used_test_definition=test_def,
            experiment_prompt_index=0,
        )
        request.session['testrun_id'] = testrun.id
    else:
        try:
            testrun = TestRun.objects.get(id=testrun_id)
            if testrun.used_test_definition is None:
                testrun.used_test_definition = test_def
                testrun.save()
            request.session['testrun_id'] = testrun.id
        except TestRun.DoesNotExist:
            testrun = TestRun.objects.create(
                consent=False,
                participant_name="Anonymous",
                current_phase='preparation',
                current_stage_index=0,
                used_test_definition=test_def,
                experiment_prompt_index=0,
            )
            request.session['testrun_id'] = testrun.id

    stages = get_all_stages_for_phase(test_def, testrun.current_phase)

    # For experiment phase, iterate over prompts for each stage
    prompts = []
    if testrun.current_phase == 'experiment':
        prompts = [p.strip() for p in test_def.prompts.split('\n')]

    if request.method == 'POST':
        if testrun.current_phase == 'experiment' and prompts:
            # Advance prompt index first
            if testrun.experiment_prompt_index < len(prompts) - 1:
                testrun.experiment_prompt_index += 1
            else:
                # Move to next stage or phase
                testrun.experiment_prompt_index = 0
                if testrun.current_stage_index < len(stages) - 1:
                    testrun.current_stage_index += 1
                else:
                    testrun.current_phase = 'evaluation'
                    testrun.current_stage_index = 0
        else:
            if testrun.current_stage_index < len(stages) - 1:
                testrun.current_stage_index += 1
            else:
                # Move to next phase or finish
                if testrun.current_phase == 'preparation':
                    testrun.current_phase = 'experiment'
                    testrun.current_stage_index = 0
                    testrun.experiment_prompt_index = 0
                elif testrun.current_phase == 'evaluation':
                    return render(request, 'testdefinition/results.html', {'testrun': testrun})
        testrun.save()
        stages = get_all_stages_for_phase(test_def, testrun.current_phase)

    # Get the current stage link
    if 0 <= testrun.current_stage_index < len(stages):
        stage_obj = stages[testrun.current_stage_index].stage
    else:
        return render(request, 'testdefinition/no_preparation_phase.html')

    # For experiment phase, pass current prompt
    current_prompt = None
    if testrun.current_phase == 'experiment' and prompts:
        if 0 <= testrun.experiment_prompt_index < len(prompts):
            current_prompt = prompts[testrun.experiment_prompt_index]
            testrun.save()

    if not stage_obj or not stage_obj.template:
        return render(request, 'testdefinition/no_template.html')

    return render(request, stage_obj.template, {'stage': stage_obj, 'testrun': testrun, 'prompt': current_prompt})
