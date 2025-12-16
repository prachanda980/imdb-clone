from rest_framework import serializers
from apps.accounts.models import CustomUser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'name', 'is_active', 'is_staff']
class RegisterSerializer(serializers.ModelSerializer):
    """
    Used for the Registration Endpoint.
    """
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True, label="Confirm password")

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'password','password2']
    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2", None)
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password']
        )
        return user
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
            'email': self.user.email,
            'name': self.user.name,
            
        }
        return data