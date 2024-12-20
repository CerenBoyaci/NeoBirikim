from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Consumption
from decimal import Decimal
from .models import Income, IncomeType
from .models import SavingGoal, Saving

class UpdateUserForm(forms.ModelForm):
    current_password = forms.CharField(widget=forms.PasswordInput, required=False, label="Mevcut Şifre")
    new_password1 = forms.CharField(widget=forms.PasswordInput, required=False, label="Yeni Şifre")
    new_password2 = forms.CharField(widget=forms.PasswordInput, required=False, label="Yeni Şifre (Tekrar)")

    class Meta:
        model = User
        fields = ['username', 'current_password', 'new_password1', 'new_password2']

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get("current_password")
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        # Mevcut şifre kontrolü
        if current_password:
            user = authenticate(username=self.instance.username, password=current_password)
            if not user:
                self.add_error('current_password', "Mevcut şifreniz yanlış.")
        
        # Yeni şifre kontrolü
        if new_password1 and new_password1 != new_password2:
            self.add_error('new_password2', "Yeni şifreler eşleşmiyor.")

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password1 = self.cleaned_data.get('new_password1')

        if new_password1:
            user.set_password(new_password1)
        
        if commit:
            user.save()
        return user
    


class ConsumptionForm(forms.ModelForm):
    food_drink = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    energy = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    water = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    clothing = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    entertainment = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    other_expenses = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    transportation = forms.DecimalField(max_digits=10, decimal_places=2, required=False)

    class Meta:
        model = Consumption
        fields = ['food_drink', 'energy', 'water', 'clothing', 'entertainment', 'other_expenses', 'transportation']
        labels = {
            'food_drink': 'Gıda ve İçecek (₺)',
            'energy': 'Enerji (₺)',
            'water': 'Su (₺)',
            'clothing': 'Giyim (₺)',
            'entertainment': 'Eğlence ve Dijital Tüketim (₺)',
            'other_expenses': 'Diğer Harcamalar (₺)',
            'transportation': 'Ulaşım Gideri (₺)',
        }
        widgets = {
            'food_drink': forms.NumberInput(attrs={'placeholder': '₺0.00'}),
            'energy': forms.NumberInput(attrs={'placeholder': '₺0.00'}),
            'water': forms.NumberInput(attrs={'placeholder': '₺0.00'}),
            'clothing': forms.NumberInput(attrs={'placeholder': '₺0.00'}),
            'entertainment': forms.NumberInput(attrs={'placeholder': '₺0.00'}),
            'other_expenses': forms.NumberInput(attrs={'placeholder': '₺0.00'}),
            'transportation': forms.NumberInput(attrs={'placeholder': '₺0.00'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        for field in self.fields:
            if cleaned_data.get(field) in [None, '', ' ']:  # Eğer alan boşsa
                cleaned_data[field] = Decimal('0.00')  # 0.00 değerini atayın
        return cleaned_data

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['income_type', 'amount']

    # Dinamik olarak gelir türlerini listeye eklemek için
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['income_type'].queryset = IncomeType.objects.all()

class CustomIncomeForm(forms.Form):
    custom_income_type = forms.CharField(max_length=100, required=False, label="Diğer Gelir Türü")
    custom_amount = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Gelir Miktarı")



class SavingGoalForm(forms.ModelForm):
    class Meta:
        model = SavingGoal
        fields = ['goal_amount']
        widgets = {
            'goal_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Hedef Tutarı (TL)'})
        }

class SavingForm(forms.ModelForm):
    class Meta:
        model = Saving
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Birikim Tutarı (TL)'})
        }