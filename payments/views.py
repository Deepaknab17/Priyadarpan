import razorpay
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Payment

# Create your views here.

# @login_required
def create_payment(request):
    if request.method == "POST":
        amount = 499 * 100  # ₹499

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY, settings.RAZORPAY_SECRET))

        order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "receipt": f"user_{request.user.id}"
        })

        Payment.objects.create(
            user=request.user,
            amount=amount,
            order_id=order['id']
        )

        return render(request, "payments/payment.html", {"order": order})

    return render(request, "payments/payment.html")


@csrf_exempt
def payment_status(request):
    if request.method == "POST":
        data = request.POST

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY, settings.RAZORPAY_SECRET))

        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature']
            })

            payment = Payment.objects.get(order_id=data['razorpay_order_id'])
            payment.razorpay_payment_id = data['razorpay_payment_id']
            payment.paid = True
            payment.save()

            return render(request, "payments/success.html")

        except:
            return render(request, "payments/failed.html")
