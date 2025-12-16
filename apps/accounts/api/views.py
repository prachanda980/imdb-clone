from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.accounts.api.serializers import UserSerializer
from apps.accounts.tasks import send_welcome_email

from apps.accounts.api.serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
)
from apps.accounts.models import CustomUser


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    def post(self, request, *args, **kwargs):
        # 1. Standard Login Process
        response = super().post(request, *args, **kwargs)
        
        # 2. Debugging Logic
        if response.status_code == 200:
            print("DEBUG: Login successful. Attempting to send email...") # <--- Debug 1
            
            user_email = request.data.get('email')
            print(f"DEBUG: User Email from request: {user_email}") # <--- Debug 2
            
            if user_email:
                from apps.accounts.models import CustomUser
                try:
                    user = CustomUser.objects.get(email=user_email)
                    print(f"DEBUG: User found: {user.name}. Triggering Celery task...") # <--- Debug 3
                    
                    # Call the task
                    send_welcome_email.delay(user.email, user.name)
                    
                    print("DEBUG: Task sent to Redis!") # <--- Debug 4
                    
                except CustomUser.DoesNotExist:
                    print("ERROR: User object not found in DB!")
                except Exception as e:
                    print(f"ERROR: Celery failed to trigger: {str(e)}")
            else:
                print("ERROR: Email field missing in request body!")

        return response


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


   