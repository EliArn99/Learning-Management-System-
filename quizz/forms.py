from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet
from django.utils import timezone

from .models import Quiz, Question, Answer


class QuizForm(forms.ModelForm):
    """
    - Validates date window (available_until after available_from)
    - Validates time_limit and num_questions_to_select
    - Better widgets for datetime-local
    """

    class Meta:
        model = Quiz
        fields = [
            "title",
            "description",
            "course",
            "available_from",
            "available_until",
            "time_limit",
            "num_questions_to_select",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "course": forms.Select(attrs={"class": "form-control"}),
            "available_from": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
            "available_until": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
            "time_limit": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "num_questions_to_select": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ensure correct parsing for datetime-local
        for f in ("available_from", "available_until"):
            self.fields[f].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]

    def clean(self):
        cleaned = super().clean()

        available_from = cleaned.get("available_from")
        available_until = cleaned.get("available_until")
        time_limit = cleaned.get("time_limit")
        num_select = cleaned.get("num_questions_to_select")

        # Time window validation
        if available_from and available_until and available_until <= available_from:
            raise ValidationError("Крайната дата трябва да е след началната дата.")

        # Optional: disallow creating quizzes fully in the past
        # (comment out if you want to allow it)
        now = timezone.now()
        if available_until and available_until < now:
            raise ValidationError("Крайната дата е в миналото. Моля, изберете валиден период.")

        # Limits validation
        if time_limit is not None and time_limit <= 0:
            raise ValidationError("Времевият лимит трябва да е положително число (в минути).")

        if num_select is not None and num_select < 0:
            raise ValidationError("Броят въпроси за случаен избор не може да е отрицателен.")

        return cleaned


class QuestionForm(forms.ModelForm):
    """
    - Validate points
    - If type is OT, answers correctness rules are enforced via AnswerFormSet clean
    """

    class Meta:
        model = Question
        fields = ["text", "points", "type"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "points": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "type": forms.Select(attrs={"class": "form-control"}),
        }

    def clean_points(self):
        points = self.cleaned_data.get("points")
        if points is None or points <= 0:
            raise ValidationError("Точките трябва да са положително число.")
        return points


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ["text", "is_correct"]
        widgets = {
            "text": forms.TextInput(attrs={"placeholder": "Текст на отговора", "class": "form-control"}),
            "is_correct": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_text(self):
        text = (self.cleaned_data.get("text") or "").strip()
        if not text:
            raise ValidationError("Текстът на отговора не може да бъде празен.")
        return text


class BaseAnswerFormSet(BaseInlineFormSet):
    """
    Enforce correctness rules per question type:

    - MC (Single correct): exactly 1 correct
    - TF (True/False): exactly 1 correct (or you can enforce exactly 1 + exactly 2 answers if you want)
    - MM (Multi correct): at least 1 correct
    - OT (Open text): no answers should be marked correct (ideally 0 answers at all)
    """

    def clean(self):
        super().clean()

        # If there is no instance/question yet, skip
        question = getattr(self, "instance", None)
        if not question:
            return

        q_type = getattr(question, "type", None)

        # Collect non-deleted forms only
        active_forms = []
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            # ignore totally empty forms
            if not form.cleaned_data.get("text") and not form.cleaned_data.get("is_correct"):
                continue
            active_forms.append(form)

        # For OT we prefer zero answers; but since UI may still show answer forms,
        # we enforce that none are marked correct.
        if q_type == "OT":
            for f in active_forms:
                if f.cleaned_data.get("is_correct"):
                    raise ValidationError("При 'Свободен текст' не трябва да има отбелязани верни отговори.")
            return

        # For non-OT, require at least 2 answers (your formset already has min_num=2,
        # but this makes it explicit when forms are blank/deleted)
        if len(active_forms) < 2:
            raise ValidationError("Трябва да има поне 2 отговора.")

        correct_count = sum(1 for f in active_forms if f.cleaned_data.get("is_correct") is True)

        if q_type in ("MC", "TF"):
            if correct_count != 1:
                raise ValidationError("За този тип въпрос трябва да има точно 1 верен отговор.")
        elif q_type == "MM":
            if correct_count < 1:
                raise ValidationError("За този тип въпрос трябва да има поне 1 верен отговор.")
        else:
            # Defensive: unknown type
            if correct_count < 1:
                raise ValidationError("Трябва да има поне 1 верен отговор.")
