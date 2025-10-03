
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
    prompt = models.TextField()

class PreparationPhaseStage(models.Model):
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
    l1 = models.ForeignKey(Language, related_name='prosodytest_l1', on_delete=models.CASCADE)
    l2 = models.ForeignKey(Language, related_name='prosodytest_l2', on_delete=models.CASCADE)
    preparation_phase = models.ManyToManyField(TestStage, through='PreparationPhaseStage', related_name='preparation_phase')
    experiment_phase = models.ManyToManyField(TestStage, through='ExperimentPhaseStage', related_name='experiment_phase')
    evaluation_phase = models.ManyToManyField(TestStage, through='EvaluationPhaseStage', related_name='evaluation_phase')
    prompts = models.TextField()

    def __str__(self):
        return f"Prosody Test: {self.l1} - {self.l2}"

class TestRun(models.Model):
    PHASE_CHOICES = [
        ('preparation', 'Preparation'),
        ('experiment', 'Experiment'),
        ('evaluation', 'Evaluation'),
    ]

    consent = models.BooleanField()
    participant_name = models.CharField(max_length=100)
    current_phase = models.CharField(max_length=20, choices=PHASE_CHOICES)
    current_stage_index = models.IntegerField()
    recording = models.ManyToManyField(Recording)
    time = models.DateTimeField(auto_now_add=True)
    used_test_definition = models.ForeignKey('ProsodyTestDefinition', null=True, blank=True, on_delete=models.SET_NULL, related_name='runs')
    experiment_prompt_index = models.IntegerField(default=0)