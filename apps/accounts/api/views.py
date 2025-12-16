from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.api.serializers import UserSerializer, RegisterSerializer
from apps.accounts.models import CustomUser

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    We extend the default JWT serializer to add 'user' details 
    into the response JSON.
    """
    def validate(self, attrs):
        # This generates the 'access' and 'refresh' tokens
        data = super().validate(attrs)
        
        # Now we add our custom data
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'name': self.user.name,
        }
        return data
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# Registration API View
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,) 
    serializer_class = RegisterSerializer