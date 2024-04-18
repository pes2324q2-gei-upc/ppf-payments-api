"""
This module contains the views for the API endpoints related to payments.
"""

from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
)
from .service.payment import processPayment

# Create your views here.


def stripe_test(request):
    return render(request, "stripe_test.html")


class CreatePaymentView(CreateAPIView):
    """
    Create a payment record.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        userId = request.user.id

        # Token payment_method obtained from frontend
        paymentMethodId = request.data.get("payment_method_id")
        routeId = request.data.get("routeID")

        if not paymentMethodId:
            return Response(
                {"error": "Payment method ID is required."}, status=HTTP_400_BAD_REQUEST
            )

        if not routeId:
            return Response({"error": "Route ID is required."}, status=HTTP_400_BAD_REQUEST)

        try:
            processPayment(routeId, userId, paymentMethodId)
            return Response(
                {"message": "Successfully joined the route and processed payment."},
                status=HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)
