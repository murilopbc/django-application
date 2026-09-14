from django.contrib import admin
from .models import (
    Professional, Patient, Procedure, Appointment,
    ToothCondition, ClinicalNote, Budget, BudgetItem, Payment
)

admin.site.register(Professional)
admin.site.register(Patient)
admin.site.register(Procedure)
admin.site.register(Appointment)
admin.site.register(ToothCondition)
admin.site.register(ClinicalNote)
admin.site.register(Budget)
admin.site.register(BudgetItem)
admin.site.register(Payment)