from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, null=True)
    amount = models.IntegerField()
    razorpay_order_id = models.CharField(max_length=1000,unique=True,null=True)
    razorpay_payment_id = models.CharField(max_length=1000, blank=True,null=True)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.username if self.user else 'Guest'} - {self.amount}"
