from rest_framework import serializers
from .models import Report, ReportUpdate


class ReportUpdateSerializer(serializers.ModelSerializer):
    """
    Nested serializer for tracking changes in report status.
    """
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ReportUpdate
        fields = [
            'id', 'old_status', 'new_status', 'notes',
            'user', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class ReportSerializer(serializers.ModelSerializer):
    """
    Main Report Serializer with:
    - IPFS CIDs
    - Media files + thumbnails
    - Blockchain hash + tx
    - Priority
    - Status
    - Nested updates (read-only)
    """

    updates = ReportUpdateSerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = [
            # Identifiers
            'id', 'reference_code',

            # Details
            'category', 'description', 'location_description',

            # GPS
            'latitude', 'longitude',

            # User info
            'is_anonymous', 'reporter_name', 'reporter_phone', 'reporter_email',

            # Media
            'media_file', 'media_thumbnail',

            # IPFS
            'ipfs_cid', 'evidence_json_cid',

            # Blockchain
            'evidence_hash', 'transaction_hash', 'is_hash_anchored',

            # Status
            'status', 'priority',

            # Meta
            'created_at', 'updated_at',

            # Nested updates
            'updates'
        ]

        read_only_fields = [
            'id', 'reference_code', 'media_thumbnail',
            'ipfs_cid', 'evidence_json_cid',
            'evidence_hash', 'transaction_hash', 'is_hash_anchored',
            'created_at', 'updated_at'
        ]

    # ------------ GPS VALIDATION ------------
    def validate_latitude(self, value):
        if value and not (-90 <= value <= 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        if value and not (-180 <= value <= 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value

    # ------------ ANONYMOUS LOGIC ------------
    def validate(self, data):
        if data.get("is_anonymous"):
            data["reporter_name"] = ""
            data["reporter_email"] = ""
            data["reporter_phone"] = ""
        return data
