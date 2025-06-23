from django.shortcuts import render

# Create your views here.


from users.models import *

from rest_framework import viewsets, permissions
from .models import Order
from .serializers import OrderSerializer

class CustomerOrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items').all()
    serializer_class = OrderSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # serializer.save(user=self.request.user) 

        serializer.save() 


