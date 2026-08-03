from django.db import models
from django.contrib.auth.models import AbstractUser, Group as BaseGroup
from django.core.exceptions import ValidationError


class User(AbstractUser):
    email = models.EmailField(blank=True, null=True, verbose_name='Endereço de email')
    observations = models.TextField(blank=True, null=True, verbose_name='Observações')

    def clean(self):
        super().clean()
        if self.email:
            email = User.objects.filter(email=self.email).exclude(pk=self.pk)
            if email.exists():
                raise ValidationError({'email': 'Já existe um usuário com este e-mail.'})


class Group(BaseGroup):
    class Meta:
        proxy = True
        verbose_name = BaseGroup._meta.verbose_name
        verbose_name_plural = BaseGroup._meta.verbose_name_plural
        app_label = 'app'


class Account(models.Model):
    description = models.CharField(max_length=100, unique=True, verbose_name='Conta')

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['description']
        verbose_name = 'Conta'
        verbose_name_plural = 'Contas'


class Type(models.Model):
    description = models.CharField(max_length=100, unique=True, verbose_name='Tipo')

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['description']
        verbose_name = 'Tipo'
        verbose_name_plural = 'Tipos'


class Method(models.Model):
    description = models.CharField(max_length=100, unique=True, verbose_name='Método')

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['description']
        verbose_name = 'Método'
        verbose_name_plural = 'Métodos'


class Category(models.Model):
    description = models.CharField(max_length=100, unique=True, verbose_name='Categoria')

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['description']
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'


class BusinessRule(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name='Conta')
    type = models.ForeignKey(Type, on_delete=models.CASCADE, verbose_name='Tipo')
    method = models.ForeignKey(Method, on_delete=models.CASCADE, verbose_name='Método')

    def __str__(self):
        return f'{self.account} / {self.type} / {self.method}'

    class Meta:
        ordering = ['account__description', 'type__description', 'method__description']
        unique_together = ('account', 'type', 'method')
        verbose_name = 'Regra de Negócio'
        verbose_name_plural = 'Regras de Negócio'


class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.PROTECT, verbose_name='Conta')
    type = models.ForeignKey(Type, on_delete=models.PROTECT, verbose_name='Tipo')
    method = models.ForeignKey(Method, on_delete=models.PROTECT, verbose_name='Método')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='Categoria')
    description = models.CharField(max_length=200, blank=True, null=True, verbose_name='Descrição')
    value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Valor')
    datetime = models.DateTimeField(verbose_name='Data e Hora')

    def clean(self):
        super().clean()
        if not BusinessRule.objects.filter(account=self.account, type=self.type, method=self.method).exists():
            raise ValidationError('Combinação de conta, tipo e método não permitida pelas regras de negócio.')

    def __str__(self):
        return f'{self.category} (R${self.value})'

    class Meta:
        ordering = ['-datetime']
        verbose_name = 'Transação'
        verbose_name_plural = 'Transações'
