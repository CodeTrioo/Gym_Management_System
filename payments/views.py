from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from gym.models import MembershipPlan, Enrollment
from payments.models import Transaction
import uuid
import hmac
import hashlib
import base64
import json
import requests


def _generate_signature(total_amount, transaction_uuid, product_code):
    secret = settings.ESEWA_SECRET
    message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    signature = base64.b64encode(
        hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    ).decode()
    return signature


@login_required
def initiate_payment(request, plan_id):
    plan = get_object_or_404(MembershipPlan, id=plan_id, is_active=True)
    transaction_uuid = str(uuid.uuid4())
    amount = plan.price
    product_code = settings.ESEWA_MERCHANT_CODE
    signature = _generate_signature(amount, transaction_uuid, product_code)

    # Create pending transaction
    transaction = Transaction.objects.create(
        user=request.user,
        amount=amount,
        product_code=product_code,
        transaction_uuid=transaction_uuid,
        plan=plan,
        status='pending',
    )

    base_url = request.build_absolute_uri('/')[:-1]
    context = {
        'plan': plan,
        'transaction': transaction,
        'esewa_url': settings.ESEWA_URL,
        'product_code': product_code,
        'amount': amount,
        'transaction_uuid': transaction_uuid,
        'signature': signature,
        'success_url': f"{base_url}/payments/success/",
        'failure_url': f"{base_url}/payments/failure/",
    }
    return render(request, 'payments/checkout.html', context)


@login_required
def payment_success(request):
    encoded_data = request.GET.get('data', '')
    if not encoded_data:
        return render(request, 'payments/failure.html', {'error': 'No payment data received.'})

    try:
        decoded = base64.b64decode(encoded_data).decode()
        data = json.loads(decoded)
        transaction_uuid = data.get('transaction_uuid')
        esewa_ref = data.get('transaction_code', '')
        status = data.get('status', '')

        transaction = get_object_or_404(Transaction, transaction_uuid=transaction_uuid, user=request.user)

        if status == 'COMPLETE':
            # Verify with eSewa status API
            verify_url = settings.ESEWA_STATUS_URL
            params = {
                'product_code': transaction.product_code,
                'total_amount': str(transaction.amount),
                'transaction_uuid': transaction_uuid,
            }
            try:
                resp = requests.get(verify_url, params=params, timeout=10)
                verified_data = resp.json()
                if verified_data.get('status') == 'COMPLETE':
                    transaction.status = 'success'
                    transaction.esewa_ref_id = esewa_ref
                    transaction.completed_at = timezone.now()
                    transaction.save()

                    # Activate membership
                    from datetime import timedelta
                    today = timezone.now().date()
                    enrollment = Enrollment.objects.create(
                        user=request.user,
                        plan=transaction.plan,
                        start_date=today,
                        end_date=today + timedelta(days=transaction.plan.duration_days),
                        is_active=True,
                        payment_ref=esewa_ref,
                    )
                    transaction.enrollment = enrollment
                    transaction.save()

                    return render(request, 'payments/success.html', {
                        'transaction': transaction,
                        'enrollment': enrollment,
                    })
            except Exception:
                pass

        transaction.status = 'failed'
        transaction.save()
        return render(request, 'payments/failure.html', {'transaction': transaction})

    except Exception as e:
        return render(request, 'payments/failure.html', {'error': str(e)})


@login_required
def payment_failure(request):
    encoded_data = request.GET.get('data', '')
    transaction = None
    if encoded_data:
        try:
            decoded = base64.b64decode(encoded_data).decode()
            data = json.loads(decoded)
            transaction_uuid = data.get('transaction_uuid')
            transaction = Transaction.objects.filter(
                transaction_uuid=transaction_uuid, user=request.user
            ).first()
            if transaction:
                transaction.status = 'failed'
                transaction.save()
        except Exception:
            pass
    return render(request, 'payments/failure.html', {'transaction': transaction})
