import razorpay,razorpay.errors
from django.conf import settings
from rest_framework.response import Response 
from rest_framework.decorators import api_view
import json
from app.models import Song
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render,get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Payment

def create_payment(req):
    amount = 499 * 100

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY, settings.RAZORPAY_SECRET))

    order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "receipt": f"user_{req.user.id if req.user.is_authenticated else 'guest'}"
    })

    Payment.objects.create(
        user=req.user if req.user.is_authenticated else None,
        amount=amount,
        razorpay_order_id=order['id']
    )

    return render(req, "payments/payment.html", {
        "id": order['id'],  
        "amount": amount,
        "key": settings.RAZORPAY_KEY
    })



def payment_status(req):
    print("POST:", req.POST)
    data = req.POST or req.GET

    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return render(req, "payments/failed.html", {"error": "Missing data"})

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY, settings.RAZORPAY_SECRET))

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        return render(req, "payments/failed.html", {"error": "Signature failed"})

    try:
        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
    except Payment.DoesNotExist:
        return render(req, "payments/failed.html", {"error": "Order not found"})

    payment.razorpay_payment_id = razorpay_payment_id
    payment.paid = True
    payment.save()


    if payment.user:
        profile = payment.user.profile

        if profile.premium_until and profile.premium_until > timezone.now():
            profile.premium_until += timedelta(days=30)
        else:
            profile.premium_until = timezone.now() + timedelta(days=30)

        profile.save()

    return render(req, "payments/success.html")



@csrf_exempt
@api_view(['POST'])  
def verify_payment(req):

    data = req.data   # 🔥 CHANGED (instead of json.loads)

    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return Response({"status": "failed", "error": "Missing data"})  # 🔥 CHANGED

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY, settings.RAZORPAY_SECRET))

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        return Response({"status": "failed", "error": "Signature failed"})  # 🔥 CHANGED

    payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)

    if not payment.paid:
        payment.razorpay_payment_id = razorpay_payment_id
        payment.paid = True
        payment.save()

        if payment.user:
            profile = payment.user.profile

            if profile.premium_until and profile.premium_until > timezone.now():
                profile.premium_until += timedelta(days=30)
            else:
                profile.premium_until = timezone.now() + timedelta(days=30)

            profile.save()

    return Response({"status": "success"})
# def pay_status(req):
#     print(req.POST)
#     roi = req.POST.get('order_id')
#     print(roi)
#     rpi = req.POST.get('razorpay_payment_id')
#     print(rpi)
#     old_roi = Order.objects.get(Order_id=roi)
#     old_roi.Razorpay_id= rpi
#     old_roi.Status=True
#     old_roi.save()
#     context = {
#     'razorpay_order_id': roi,
#     'razorpay_payment_id': rpi,
#     'amount': old_roi.Amount 
#     }
#     return render(req,'sucess.html',context)