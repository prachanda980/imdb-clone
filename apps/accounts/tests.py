from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken

class AuthTestCase(APITestCase):
    def setUp(self):
        # Create a test user for login & token refresh tests
        self.user = CustomUser.objects.create_user(
            email='testuser@example.com',
            name='Test User',
            password='testpassword123'
        )
        # URLs
        self.register_url = reverse('register')  
        self.login_url = reverse('login')  
        self.refresh_url = reverse('token_refresh')     

    # ---------------- Registration ----------------
    def test_registration_success(self):
        data = {
            'email': 'newuser@example.com',
            'name': 'New User',
            'password': 'newpassword123',
            'password2': 'newpassword123'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.filter(email='newuser@example.com').exists(), True)

    def test_registration_password_mismatch(self):
        data = {
            'email': 'newuser2@example.com',
            'name': 'New User 2',
            'password': 'pass123',
            'password2': 'pass456'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    # ---------------- Login ----------------
    def test_login_jwt_success(self):
        data = {
            'email': 'testuser@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        # Save access token for future tests
        self.access_token = response.data['access']
        self.refresh_token = response.data['refresh']

    def test_login_jwt_wrong_password(self):
        data = {
            'email': 'testuser@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---------------- Token Refresh ----------------
    def test_token_refresh_success(self):
        # Get refresh token
        refresh = RefreshToken.for_user(self.user)
        data = {'refresh': str(refresh)}
        response = self.client.post(self.refresh_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_refresh_invalid(self):
        data = {'refresh': 'invalidtoken'}
        response = self.client.post(self.refresh_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
