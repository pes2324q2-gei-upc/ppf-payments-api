"""
This module contains the views for the API endpoints related to payments.
"""

from datetime import datetime
from django.shortcuts import render
from django.conf import settings
from rest_framework.generics import CreateAPIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
)
from common.models.user import User
from common.models.route import Route
from common.models.payment import Payment
import stripe

# Create your views here.


def stripe_test(request):
    """
    Basic HTML page to test the Stripe integration.
    """
    return render(request, "stripe_test.html")


class CreatePaymentView(CreateAPIView):
    """
    Create a payment using Stripe API.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Token payment_method obtained from frontend
        paymentMethodId = request.data.get("payment_method_id")
        routeId = request.data.get("routeID")

        if not paymentMethodId:
            return Response(
                {"error": "Payment method ID is required."}, status=HTTP_400_BAD_REQUEST
            )

        if not routeId:
            return Response({"error": "Route ID is required."}, status=HTTP_400_BAD_REQUEST)

        route = Route.objects.get(id=routeId)
        user = User.objects.get(id=request.user.id)
        priceForStripe = route.price * 100  # Stripe manage amount in cents

        if Payment.objects.filter(user=user, route=route).exists():
            return Response(
                {"error": "You have already paid for this route."},
                status=HTTP_400_BAD_REQUEST,
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY

        paymentIntent = stripe.PaymentIntent.create(
            amount=int(priceForStripe),
            currency="eur",
            payment_method=paymentMethodId,  # Payment method ID from the client
            confirm=True,  # Create and Confirm at the same time
            receipt_email="powerpathfinderppf@gmail.com",
            automatic_payment_methods={  # enable no redirect
                "enabled": True,
                "allow_redirects": "never",
            },
            # Specify a return_url if you want to redirect the user back to a specific page after successfull payment
        )

        if paymentIntent.status == "succeeded":
            Payment.objects.create(
                user=user,
                route=route,
                amount=route.price,
                date=datetime.now(),
                description=f"Joined route {routeId} for ${route.price} at {datetime.now()}",
                paymentIntentId=paymentIntent.id,
            )

            return Response({"message": "Payment processed successfully."}, status=HTTP_200_OK)
        else:
            return Response({"error": "Payment failed"}, status=HTTP_400_BAD_REQUEST)


class CreateRefundView(CreateAPIView):
    """
    Create a refund using Stripe API.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        paymentIntentId = request.data.get("payment_intent_id")

        if not paymentIntentId:
            return Response(
                {"error": "Payment intent ID is required."}, status=HTTP_400_BAD_REQUEST
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY

        refund = stripe.Refund.create(
            payment_intent=paymentIntentId,
        )

        if refund.status == "succeeded":
            return Response({"message": "Refund processed successfully."}, status=HTTP_200_OK)
        else:
            return Response({"Refund failed"}, status=HTTP_400_BAD_REQUEST)
