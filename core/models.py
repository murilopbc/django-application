from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone


# ---------------------------------------------------------
# PROFISSIONAL
# ---------------------------------------------------------
class Professional(models.Model):
    """Vincula um usuário do Django a um perfil de profissional (dentista)."""

    class Specialty(models.TextChoices):
        GENERAL = "GERAL", "Clínico Geral"
        ORTHO = "ORTO", "Ortodontia"
        ENDO = "ENDO", "Endodontia"
        IMPLANT = "IMPL", "Implantodontia"
        PERIO = "PERIO", "Periodontia"
        PEDIATRIC = "PEDO", "Odontopediatria"
        SURGERY = "CIR", "Cirurgia Bucomaxilofacial"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="professional")
    cro = models.CharField("CRO", max_length=20, unique=True)
    cro_state = models.CharField("UF do CRO", max_length=2)
    specialty = models.CharField(max_length=10, choices=Specialty.choices)
    phone = models.CharField(max_length=20, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Profissional"
        verbose_name_plural = "Profissionais"
        permissions = [
            ("view_all_agendas", "Pode visualizar agenda de todos os profissionais"),
            ("manage_financeiro", "Pode gerenciar módulo financeiro"),
        ]

    def __str__(self):
        return f"Dr(a). {self.user.get_full_name()} - {self.cro}"


# ---------------------------------------------------------
# PACIENTE
# ---------------------------------------------------------
class Patient(models.Model):
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$", message="Telefone deve estar em formato válido."
    )

    full_name = models.CharField("Nome completo", max_length=200)
    cpf = models.CharField("CPF", max_length=14, unique=True)
    birth_date = models.DateField("Data de nascimento")
    phone = models.CharField(validators=[phone_regex], max_length=17)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)

    # Histórico de saúde relevante
    allergies = models.TextField("Alergias", blank=True)
    medications = models.TextField("Medicações em uso", blank=True)
    health_conditions = models.TextField("Condições de saúde relevantes", blank=True)

    # Convênio
    has_insurance = models.BooleanField("Possui convênio", default=False)
    insurance_name = models.CharField(max_length=100, blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)

    # LGPD
    consent_data_processing = models.BooleanField("Consentimento LGPD", default=False)
    consent_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name

    @property
    def age(self):
        today = timezone.now().date()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )


# ---------------------------------------------------------
# PROCEDIMENTO (catálogo de serviços)
# ---------------------------------------------------------
class Procedure(models.Model):
    name = models.CharField("Nome do procedimento", max_length=150)
    code = models.CharField("Código (TUSS/tabela própria)", max_length=20, blank=True)
    description = models.TextField(blank=True)
    default_price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_duration = models.PositiveIntegerField("Duração estimada (min)", default=30)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Procedimento"
        verbose_name_plural = "Procedimentos"

    def __str__(self):
        return self.name


# ---------------------------------------------------------
# AGENDAMENTO
# ---------------------------------------------------------
class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "AGENDADA", "Agendada"
        CONFIRMED = "CONFIRMADA", "Confirmada"
        IN_PROGRESS = "EM_ATENDIMENTO", "Em atendimento"
        COMPLETED = "CONCLUIDA", "Concluída"
        CANCELLED = "CANCELADA", "Cancelada"
        NO_SHOW = "FALTA", "Falta"

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="appointments")
    professional = models.ForeignKey(Professional, on_delete=models.PROTECT, related_name="appointments")
    procedure = models.ForeignKey(Procedure, on_delete=models.SET_NULL, null=True, related_name="appointments")

    start_datetime = models.DateTimeField("Início")
    end_datetime = models.DateTimeField("Fim")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    notes = models.TextField("Observações", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Consulta"
        verbose_name_plural = "Consultas"
        ordering = ["start_datetime"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_datetime__gt=models.F("start_datetime")),
                name="appointment_end_after_start",
            )
        ]

    def __str__(self):
        return f"{self.patient} - {self.start_datetime:%d/%m/%Y %H:%M}"


# ---------------------------------------------------------
# ODONTOGRAMA / PRONTUÁRIO
# ---------------------------------------------------------
class ToothCondition(models.Model):
    """Registra o estado de um dente específico para um paciente, em um dado momento."""

    class Condition(models.TextChoices):
        HEALTHY = "SAUDAVEL", "Saudável"
        CAVITY = "CARIE", "Cárie"
        RESTORED = "RESTAURADO", "Restaurado"
        EXTRACTED = "EXTRAIDO", "Extraído"
        IMPLANT = "IMPLANTE", "Implante"
        CANAL = "CANAL", "Tratamento de canal"
        CROWN = "COROA", "Coroa"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="tooth_records")
    tooth_number = models.PositiveSmallIntegerField("Número do dente (FDI)")  # 11-48
    condition = models.CharField(max_length=20, choices=Condition.choices)
    appointment = models.ForeignKey(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name="tooth_records"
    )
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro dentário"
        verbose_name_plural = "Odontograma"
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"Dente {self.tooth_number} - {self.get_condition_display()}"


class ClinicalNote(models.Model):
    """Anotação clínica de uma consulta (evolução do prontuário)."""

    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name="clinical_note")
    description = models.TextField("Descrição do atendimento")
    prescription = models.TextField("Prescrição", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Anotação clínica"
        verbose_name_plural = "Anotações clínicas"

    def __str__(self):
        return f"Nota - {self.appointment}"


# ---------------------------------------------------------
# ORÇAMENTO / FINANCEIRO
# ---------------------------------------------------------
class Budget(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDENTE", "Pendente"
        APPROVED = "APROVADO", "Aprovado"
        REJECTED = "REJEITADO", "Rejeitado"

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="budgets")
    professional = models.ForeignKey(Professional, on_delete=models.PROTECT, related_name="budgets")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Orçamento"
        verbose_name_plural = "Orçamentos"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    def __str__(self):
        return f"Orçamento #{self.pk} - {self.patient}"


class BudgetItem(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="items")
    procedure = models.ForeignKey(Procedure, on_delete=models.PROTECT)
    tooth_number = models.PositiveSmallIntegerField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.procedure} x{self.quantity}"


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "DINHEIRO", "Dinheiro"
        CARD_CREDIT = "CARTAO_CREDITO", "Cartão de Crédito"
        CARD_DEBIT = "CARTAO_DEBITO", "Cartão de Débito"
        PIX = "PIX", "Pix"
        INSURANCE = "CONVENIO", "Convênio"

    budget = models.ForeignKey(Budget, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices)
    paid_at = models.DateTimeField(default=timezone.now)
    installment_number = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"

    def __str__(self):
        return f"R${self.amount} - {self.get_method_display()}"