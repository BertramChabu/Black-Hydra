from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ScanResult 
from .tasks import run_port_scan
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django_otp import user_has_device

import qrcode as qr
import base64
from io import BytesIO
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.decorators import permission_classes
from django.contrib.auth.models import Group
from rest_framework.exceptions import AuthenticationFailed











class MFATokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user
        if user_has_device(user):
            mfa_token = self.context['request'].data.get('otp_token')
            device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
            if not (device and device.verify_token(mfa_token)):
                raise AuthenticationFailed("MFA token is invalid or missing")
        return data
    

class MFATokenObtainPairView(TokenObtainPairSerializer):
    serializer_class = MFATokenObtainPairSerializer


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='admin').exists()
    

class IsAnalystOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name__in=['admin', 'analyst']).exists()
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_mfa_qr(request):
    user = request.user


    TOTPDevice.objects .filter(user=user).delete()

    # create a new TOTP device
    device = TOTPDevice.objects.create(user=user, name ='default', confirmed=False)

    otp_url = device.config_url

    img = qr.make(otp_url)
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_image = base64.b64encode(buffer.getvalue()).decode()

    return Response({
        'otp_url': otp_url,
        'qr_code_base64': qr_image,

    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_mfa(request):
    otp_token = request.data.get("otp_token")
    user = request.user


    device = TOTPDevice.objects.filter(user=user, confrimed=False).first()
    if device and device.verify_token(otp_token):
        device.confirmed = True
        device.save()
        return Response({"message": "MFA setup complete."})
    return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)


    

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def start_scan(request):
    target = request.data.get('target')
    if not target:
        return Response({"error": "Target is required"}, status=status.HTTP_404_NOT_FOUND)
    
    scan = ScanResult.objects.create(target=target)
    run_port_scan.delay(scan.id)

    return Response({"message" : "Scan Started", "scan_id" : scan.id})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAnalystOrAdmin])
def scan_status(request, scan_id):
    try:
        scan = ScanResult.objects.get(id=scan_id)
        return Response({
            "target": scan.target,
            "status" : scan_status,
            "result": scan.result,
            "created_at": scan.created_at
        })
    except ScanResult.DoesNotExist:
        return Response({"error": "Scan Not Found"}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def list_scans(request):
    scans = ScanResult.objects.all().order_by('-created_at')
    data = []
    for scan in scans:
        data.append({
            "id": scan.id,
            "target": scan.target,
            "status": scan.status,
            "created_at":
            scan.created_at,
        })
    return Response(data, status=status.HTTP_200_OK)
