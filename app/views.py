import base64
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from .models import Transaction


@csrf_exempt
@require_GET
def api_transactions(request):
    user = None
    prefix, _, credentials = request.headers.get('Authorization', '').partition(' ')

    if prefix == 'Basic' and credentials.strip():
        try:
            username, _, password = base64.b64decode(credentials.strip()).decode().partition(':')
            user = authenticate(request, username=username, password=password)
        except (ValueError, UnicodeDecodeError):
            user = None

    if user is None or not user.is_active:
        response = JsonResponse({'detail': 'Credenciais inválidas.'}, status=401)
        response['WWW-Authenticate'] = 'Basic realm="api", charset="UTF-8"'
        return response

    queryset = Transaction.objects.select_related('user', 'account', 'category')

    if not (user.is_staff and user.has_perm('app.view_transaction')):
        queryset = queryset.filter(user=user)

    return JsonResponse([
        {
            'holder': transaction.user.get_full_name() or transaction.user.get_username(),
            'account': transaction.account.description,
            'type': transaction.get_type_display(),
            'method': transaction.get_method_display(),
            'category': transaction.category_display,
            'description': transaction.description,
            'value': float(transaction.value),
            'datetime': transaction.datetime.isoformat()
        }
        for transaction in queryset.iterator()
    ], safe=False)
