from django import forms

from .models import Course


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["name", "description", "university_name", "price"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Course Name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Course Description",
                    "rows": 5,
                }
            ),
            "university_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "University Name",
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                }
            ),
        }

    def clean_price(self):
        price = self.cleaned_data["price"]

        if price < 0:
            raise forms.ValidationError("Price cannot be negative.")

        return price
