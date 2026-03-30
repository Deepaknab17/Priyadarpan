import razorpay,razorpay.errors
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Payment

# Create your views here.

# @login_required
def create_payment(req):
    if req.method == "POST":
        amount = 499 * 100  # ₹499

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY, settings.RAZORPAY_SECRET))

        order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "receipt": f"user_{req.user.id}"
        })

        Payment.objects.create(
            user=req.user if req.user.is_authenticated else None,
            amount=amount,
            order_id=order['id']
        )

        return render(req, "payments/payment.html", {
    "order": order,
    "key": settings.RAZORPAY_KEY
})
    return render(req, "payments/payment.html")

@csrf_exempt
def payment_status(req):
    data = req.POST or req.GET
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY, settings.RAZORPAY_SECRET))
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')
    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return render(req, "payments/failed.html", {"error": "Missing data"})
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        return render(req, "payments/failed.html", {"error": "Signature failed"})
    try:
        payment = Payment.objects.get(order_id=razorpay_order_id)
    except Payment.DoesNotExist:
        return render(req, "payments/failed.html", {"error": "Order not found"})
    payment.razorpay_payment_id = razorpay_payment_id
    payment.paid = True
    payment.save()
    if payment.user:
        profile = payment.user.profile
        if profile.role == "user":
            profile.is_premium = True
            profile.save()
    return render(req, "payments/success.html")