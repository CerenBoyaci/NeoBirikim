from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
class Item(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField()
    

class Consumption(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food_drink = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    energy = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    water = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    clothing = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    entertainment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transportation = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Ulaşım Gideri
    created_at = models.DateTimeField(default=timezone.now)  # Otomatik tarih alanı

    def __str__(self):
        return f'{self.user.username} - {self.food_drink}, {self.energy}, {self.water}, {self.clothing}, {self.entertainment}, {self.other_expenses}, {self.transportation}'

class IncomeType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    income_type = models.ForeignKey(IncomeType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.income_type.name}: {self.amount} TL"
    
class SavingGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saving_goals')
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Hedef Tutar")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.goal_amount} TL"

class Saving(models.Model):
    goal = models.ForeignKey(SavingGoal, on_delete=models.CASCADE, related_name='savings')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Birikim Tutarı")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.goal.user.username} - {self.amount} TL"

