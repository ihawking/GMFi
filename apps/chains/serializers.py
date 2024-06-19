from rest_framework import serializers

from chains.models import Network


class NetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Network
        fields = (
            "chain_id",
            "name",
        )
