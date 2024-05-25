from django import forms
from management import models

class GroupTrainingForm(forms.ModelForm):
    day = forms.ChoiceField(choices=models.GroupTraining.DAY_CHOICES)
    start_hour = forms.ChoiceField(choices=models.GroupTraining.START_HOUR_CHOICES)

    class Meta:
        model = models.GroupTraining
        fields = ['trainer', 'day', 'start_hour', 'duration', 'max_participants', 'title', 'image']


class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = models.SubscriptionPlan
        fields = ['name', 'plan_type', 'monthly_price', 'age_discount']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'plan_type': forms.Select(attrs={'class': 'form-control'}),
            'monthly_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'age_discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class DurationDiscountForm(forms.Form):
    discount_1 = forms.DecimalField(max_digits=5, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    discount_3 = forms.DecimalField(max_digits=5, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    discount_6 = forms.DecimalField(max_digits=5, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    discount_12 = forms.DecimalField(max_digits=5, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))