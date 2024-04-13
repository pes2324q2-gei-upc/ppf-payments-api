from rest_framework import serializers
from common.models.payment import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Payment model.
    """

    class Meta:
        model = Payment
        exclude = ["paymentIntentId"]
