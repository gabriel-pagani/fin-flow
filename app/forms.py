import csv
import io
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Account, BusinessRule, Method, Transaction, Type, User


HEADER = ['Data', 'Valor', 'Identificador', 'Descrição']

# Um minuto por transação, sem ultrapassar o dia (00:00 até 23:59).
MAX_MINUTES = 24 * 60 - 1


def decode(raw):
    for encoding in ('utf-8-sig', 'latin-1'):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValidationError('Não foi possível ler o arquivo. Envie o CSV original exportado pelo Nubank.')


class TransactionImportForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all(), label='Usuário', help_text='Titular das transações importadas.')
    account = forms.ModelChoiceField(queryset=Account.objects.all(), label='Conta', help_text='Conta na qual as transações do extrato serão registradas.')
    file = forms.FileField(label='Arquivo', help_text='Arquivo CSV exportado pelo Nubank.')

    def clean_file(self):
        file = self.cleaned_data['file']

        if not file.name.lower().endswith('.csv'):
            raise ValidationError('O arquivo deve estar no formato CSV.')

        reader = csv.DictReader(io.StringIO(decode(file.read())))

        if reader.fieldnames != HEADER:
            raise ValidationError(f'Cabeçalho inesperado. Esperado: {", ".join(HEADER)}.')

        rows = []
        minutes = {}
        occurrences = {}
        for number, row in enumerate(reader, start=2):
            identifier = (row['Identificador'] or '').strip()[:87]
            if not identifier:
                raise ValidationError(f'Linha {number}: identificador ausente.')

            # O Nubank reaproveita o identificador em lançamentos relacionados (um
            # estorno carrega o identificador da transação estornada), então cada
            # repetição recebe um sufixo para que ambas as linhas sejam importadas.
            occurrence = occurrences[identifier] = occurrences.get(identifier, 0) + 1
            if occurrence > 1:
                identifier = f'{identifier}#{occurrence}'

            try:
                date = datetime.strptime((row['Data'] or '').strip(), '%d/%m/%Y')
            except ValueError:
                raise ValidationError(f'Linha {number}: data inválida ({row["Data"]}).')

            try:
                value = Decimal((row['Valor'] or '').strip())
            except InvalidOperation:
                raise ValidationError(f'Linha {number}: valor inválido ({row["Valor"]}).')

            if not value:
                raise ValidationError(f'Linha {number}: valor não pode ser zero.')

            # O extrato só informa a data, então cada transação do mesmo dia recebe
            # um minuto a mais, preservando a ordem em que aparecem no arquivo.
            minute = minutes[date] = minutes.get(date, -1) + 1
            if minute > MAX_MINUTES:
                raise ValidationError(f'Linha {number}: o extrato tem mais de {MAX_MINUTES + 1} transações em {date:%d/%m/%Y}.')

            date += timedelta(minutes=minute)

            if settings.USE_TZ:
                date = timezone.make_aware(date)

            rows.append({
                'external_id': identifier,
                'type': Type.IN if value > 0 else Type.OUT,
                'method': Method.NOT_APPLICABLE if value > 0 else Method.DEBIT,
                'description': (row['Descrição'] or '').strip()[:200] or None,
                'value': abs(value),
                'datetime': date,
            })

        if not rows:
            raise ValidationError('O arquivo não contém transações.')

        self.cleaned_data['rows'] = rows
        return file

    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        rows = cleaned_data.get('rows')

        if account and rows:
            # Transações já importadas para esta conta são ignoradas, permitindo
            # reenviar o mesmo extrato sem duplicar lançamentos.
            imported = set(Transaction.objects.filter(
                account=account,
                external_id__in=[row['external_id'] for row in rows],
            ).values_list('external_id', flat=True))

            rows = [row for row in rows if row['external_id'] not in imported]
            cleaned_data['rows'] = rows
            cleaned_data['skipped'] = len(imported)

            if not rows:
                raise ValidationError('Todas as transações deste arquivo já foram importadas.')

            combinations = {(row['type'], row['method']) for row in rows}
            allowed = set(BusinessRule.objects.filter(account=account).values_list('type', 'method'))
            for type, method in sorted(combinations - allowed):
                raise ValidationError(f'A conta {account} não permite {Type(type).label.lower()} em {Method(method).label.lower()}, necessário para importar o extrato.')

        return cleaned_data

    def save(self):
        user = self.cleaned_data['user']
        account = self.cleaned_data['account']

        # Salvo individualmente (e não em bulk_create) para que o django-reversion,
        # que depende do sinal post_save, registre uma versão de cada transação.
        return [
            Transaction.objects.create(
                user=user,
                account=account,
                category=None,
                **row,
            )
            for row in self.cleaned_data['rows']
        ]
