import random
from django.db import models

class Language(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class TestStage(models.Model):
    name = models.CharField(max_length=100)
    template = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.template})"

class Recording(models.Model):
    file_path = models.CharField(max_length=255)
    trial = models.TextField()
    testrun = models.ForeignKey('TestRun', on_delete=models.CASCADE, related_name='recordings')

    def __str__(self):
        return f"Recording {self.pk} for Run {self.testrun_id}: {self.file_path}"[:80]

class PreparationPhaseStage(models.Model):
    prosody_test = models.ForeignKey('ProsodyTestDefinition', on_delete=models.CASCADE)
    stage = models.ForeignKey(TestStage, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.stage} (Order: {self.order})"

class PractiseTestPhaseStage(models.Model):
    prosody_test = models.ForeignKey('ProsodyTestDefinition', on_delete=models.CASCADE)
    stage = models.ForeignKey(TestStage, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('prosody_test', 'stage')

    def __str__(self):
        return f"{self.stage} (Order: {self.order})"

class MainTestPhaseStage(models.Model):
    prosody_test = models.ForeignKey('ProsodyTestDefinition', on_delete=models.CASCADE)
    stage = models.ForeignKey(TestStage, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('prosody_test', 'stage')

    def __str__(self):
        return f"{self.stage} (Order: {self.order})"

class ExperimentPhaseStage(models.Model):
    prosody_test = models.ForeignKey('ProsodyTestDefinition', on_delete=models.CASCADE)
    stage = models.ForeignKey(TestStage, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('prosody_test', 'stage')

    def __str__(self):
        return f"{self.stage} (Order: {self.order})"

class EvaluationPhaseStage(models.Model):
    prosody_test = models.ForeignKey('ProsodyTestDefinition', on_delete=models.CASCADE)
    stage = models.ForeignKey(TestStage, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('prosody_test', 'stage')

    def __str__(self):
        return f"{self.stage} (Order: {self.order})"


class ProsodyTestDefinition(models.Model):
    l2 = models.ForeignKey(Language, related_name='prosodytest_l2', on_delete=models.CASCADE)
    preparation_phase = models.ManyToManyField(TestStage, through='PreparationPhaseStage', related_name='preparation_phase')
    practise_test_phase = models.ManyToManyField(TestStage, through='PractiseTestPhaseStage', related_name='practise_test_phase')
    main_test_phase = models.ManyToManyField(TestStage, through='MainTestPhaseStage', related_name='main_test_phase')
    evaluation_phase = models.ManyToManyField(TestStage, through='EvaluationPhaseStage', related_name='evaluation_phase')
    main_trials = models.TextField(help_text='Trials for the main test (one per line), separate context and prompt with |', blank=True, null=True)
    practise_trials = models.TextField(help_text='Trials for the practise test (one per line), separate context and prompt with |', blank=True, null=True)

    def __str__(self):
        return f"Prosody Test: {self.l2}"

class TestRun(models.Model):
    PHASE_CHOICES = [
        ('preparation', 'Preparation'),
        ('practise', 'Practise'),
        ('main', 'Main'),
        ('evaluation', 'Evaluation'),
    ]

    consent = models.BooleanField()
    l1 = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    current_phase = models.CharField(max_length=20, choices=PHASE_CHOICES)
    current_stage_index = models.IntegerField()
    time = models.DateTimeField(auto_now_add=True)
    used_test_definition = models.ForeignKey('ProsodyTestDefinition', null=True, blank=True, on_delete=models.SET_NULL, related_name='runs')
    experiment_trial_index = models.IntegerField(default=0)
    main_trial_order = models.TextField(blank=True, null=True)


    def save(self, *args, **kwargs):
        # Only fill main_trial_order if not set
        if not self.main_trial_order and self.used_test_definition and self.used_test_definition.main_trials:
            trials = [t.strip() for t in self.used_test_definition.main_trials.split('\n') if t.strip()]
            order = list(range(len(trials)))
            random.shuffle(order)
            self.main_trial_order = ','.join(str(i) for i in order)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Run {self.pk}: {getattr(self, 'participant_name', '')}"