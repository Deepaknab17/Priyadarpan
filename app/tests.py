from django.test import TestCase
from datetime import datetime,timedelta
from django.utils import timezone

# Create your tests here.
# n=datetime.now()
# print(n)
# delta=timedelta(minutes=30)
# print(delta)

time=timezone.now()
print(time)
print(timezone.LocalTimezone)