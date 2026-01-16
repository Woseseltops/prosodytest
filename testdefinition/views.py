import base64

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import ProsodyTestDefinition, PreparationPhaseStage, TestRun, PractiseTestPhaseStage, MainTestPhaseStage, EvaluationPhaseStage, Recording

def get_all_stages_for_phase(test_def, phase):

    if phase == 'preparation':
        return list(PreparationPhaseStage.objects.filter(prosody_test=test_def).order_by('order'))
    elif phase == 'practise':
        return list(PractiseTestPhaseStage.objects.filter(prosody_test=test_def).order_by('order'))
    elif phase == 'main':
        return list(MainTestPhaseStage.objects.filter(prosody_test=test_def).order_by('order'))
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
            experiment_trial_index=0,
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
                experiment_trial_index=0,
            )
            request.session['testrun_id'] = testrun.id

    stages = get_all_stages_for_phase(test_def, testrun.current_phase)

    print(request.POST)

    if request.POST.get('user_data') or request.POST.get('audio_data'):
        process_user_data(request.POST, testrun)

    # For practise and main test phases, iterate over trials for each stage
    trials = []
    if testrun.current_phase == 'practise':
        trials = [p.strip() for p in (test_def.practise_trials or '').split('\n') if p.strip()]
    elif testrun.current_phase == 'main':
        trials = [p.strip() for p in (test_def.main_trials or '').split('\n') if p.strip()]

    if request.method == 'POST':
        if testrun.current_phase in ['practise', 'main'] and trials:
            # Cycle through stages for each trial
            total_trials = len(trials)
            total_stages = len(stages)
            current_flat_index = testrun.experiment_trial_index
            max_flat_index = total_trials * total_stages - 1

            if current_flat_index < max_flat_index:
                testrun.experiment_trial_index += 1
            else:
                # Move to next phase
                if testrun.current_phase == 'practise':
                    testrun.current_phase = 'main'
                    testrun.current_stage_index = 0
                    testrun.experiment_trial_index = 0
                else:
                    # Move to evaluation phase
                    testrun.current_phase = 'evaluation'
                    testrun.current_stage_index = 0
                    testrun.experiment_trial_index = 0
            testrun.save()
            stages = get_all_stages_for_phase(test_def, testrun.current_phase)
        else:
            if testrun.current_stage_index < len(stages) - 1:
                testrun.current_stage_index += 1
            else:
                # Move to next phase or finish
                if testrun.current_phase == 'preparation':
                    testrun.current_phase = 'practise'
                    testrun.current_stage_index = 0
                    testrun.experiment_trial_index = 0
                elif testrun.current_phase == 'evaluation':
                    return render(request, 'testdefinition/results.html', {'testrun': testrun})
            testrun.save()
            stages = get_all_stages_for_phase(test_def, testrun.current_phase)

    # Get the current stage and trial for practise and main test phases
    if testrun.current_phase in ['practise', 'main'] and trials:
        total_stages = len(stages)
        total_trials = len(trials)
        flat_index = testrun.experiment_trial_index
        if 0 <= flat_index < total_stages * total_trials:
            stage_index = flat_index % total_stages
            trial_index = flat_index // total_stages
            stage_obj = stages[stage_index].stage
            current_trial = trials[trial_index]
        else:
            return render(request, 'testdefinition/no_preparation_phase.html')
    else:
        current_trial = None
        if 0 <= testrun.current_stage_index < len(stages):
            stage_obj = stages[testrun.current_stage_index].stage
        else:
            return render(request, 'testdefinition/no_preparation_phase.html')

    if not stage_obj or not stage_obj.template:
        return render(request, 'testdefinition/no_template.html')

    # If using context.html or context_trial.html, split trial by '|'
    if stage_obj.template in ['context.html', 'context_trial.html'] and current_trial:
        return render(request, stage_obj.template, {'stage': stage_obj, 'testrun': testrun,'context': current_trial.split('|')[0].strip()})
    # If using prompt.html, only show the part after the first |
    elif stage_obj.template == 'prompt.html' and current_trial:
        return render(request, stage_obj.template, {'stage': stage_obj, 'testrun': testrun, 'prompt': current_trial.split('|')[1].strip()})
    else:
        return render(request, stage_obj.template, {'stage': stage_obj, 'testrun': testrun, 'prompt': current_trial})

def process_user_data(post_data, testrun):

    if post_data.get('audio_data'):
        audio_data = post_data['audio_data']
        audio_bytes = base64.b64decode(audio_data)
        trial_text = post_data.get('trial', '')

        # Create Recording entry first
        recording_entry = Recording.objects.create(file_path='', trial=trial_text, testrun=testrun)
        filename = f"audio/{testrun.id}_{recording_entry.pk}.wav"
        with open(filename, "wb") as f:
            f.write(audio_bytes)

        # Update file_path and save
        recording_entry.file_path = filename
        recording_entry.save()

        # Link to TestRun
        testrun.recordings.add(recording_entry)

    elif post_data.get('user_data'):
        participant_name = post_data.get('participant_name', 'Anonymous')
        l1_text = post_data.get('l1', '')
        country_text = post_data.get('country', '')
        testrun.participant_name = participant_name
        testrun.l1 = l1_text
        testrun.country = country_text
        testrun.save()