from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.accounts.api.serializers import UserSerializer

from apps.accounts.api.serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
)
from apps.accounts.models import CustomUser


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# Registration API View
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can see only themselves
        return CustomUser.objects.filter(id=self.request.user.id)

    def get_object(self):
        # Return the logged-in user
        return self.request.user