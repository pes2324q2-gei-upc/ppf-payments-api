import datetime
from django.conf import settings
from rest_framework.exceptions import ValidationError
from common.models.route import Route, RoutePassenger
from common.models.payment import Payment, Refund
import stripe


def processPayment(routeId: int, passengerId: int, paymentMethodId: str):
    """
    Process the payment for a route.

    Args:
        route_id (int): The ID of the route.
        user_id (int): The ID of the user.
        payment_method_id (str): The ID of the payment method.
    """
    route = Route.objects.get(id=routeId)
    price = route.price

    stripe.api_key = settings.STRIPE_SECRET_KEY

    paymentIntent = stripe.PaymentIntent.create(
        amount=int(price * 100),
        currency="usd",
        payment_method=paymentMethodId,  # Payment method ID from the client
        confirm=True,  # Create and Confirm at the same time
    )

    if paymentIntent.status == "succeeded":
        # If payment is successful, create a transaction record
        Payment.objects.create(
            user=passengerId,
            amount=route.price,
            date=datetime.now(),  # type: ignore
            description=f"Joined route {routeId} for ${route.price} at {datetime.now()}",  # type: ignore
            paymentIntentId=paymentIntent.id,
        )

        RoutePassenger.objects.create(route_id=routeId, passenger_id=passengerId)
        return {"message": "Successfully joined the route and processed payment.", "status": 200}
    else:
        raise ValidationError("Payment failed", 400)


def processRefund(payment: Payment):
    """
    Process a refund for a payment.

    Args:
        payment_intent_id (str): The ID of the payment intent.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY

    paymentIntentId = payment.paymentIntentId
    refund = stripe.Refund.create(payment_intent=paymentIntentId)

    if refund.status == "succeeded":
        # If refund is successful, create a refund record
        Refund.objects.create(
            payment=payment,
            date=datetime.now(),  # type: ignore
            reason="User left the route less than 24 hours before departure",
        )

        return {"message": "Refund processed successfully.", "status": 200}
    else:
        raise ValidationError("Refund failed", 400)
