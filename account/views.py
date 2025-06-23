from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.permissions import IsAuthenticated,AllowAny
from .serializers import (

    UserRegistrationSerializer, 
    UserLoginSerializer, 
    UserUpdateSerializer,
    UserSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
from .token import user_tokenizer_generate


@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    """
    User Registration API
    """
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Send email verification
        current_site = get_current_site(request)
        subject = 'Account verification email'
        message = render_to_string('account/registeration/email-verification.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': user_tokenizer_generate.make_token(user),
        })
        
        user.email_user(subject=subject, message=message)
        
        return Response({
            'message': 'Registration successful. Please check your email for verification.',
            'user_id': user.id,
            'username': user.username,
            'email': user.email
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])

def login_api(request):
    """
    User Login API
    """
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Create or get token for authentication
        token, created = Token.objects.get_or_create(user=user)
        
        # Login user
        login(request, user)
        
        return Response({
            'message': 'Login successful',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """
    User Logout API
    """
    try:
        # Delete the token
        request.user.auth_token.delete()
        logout(request)
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except:
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_api(request):
    """
    Dashboard API - Get user data
    """
    serializer = UserSerializer(request.user)
    return Response({
        'message': 'Dashboard data retrieved successfully',
        'user': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])

@permission_classes([IsAuthenticated])
def profile_management_api(request):
    """
    Profile Management API
    """
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        serializer = UserUpdateSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account_api(request):
    """
    Delete Account API
    """
    user = request.user
    user.delete()
    
    return Response({
        'message': 'Account deleted successfully'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def email_verification_api(request):
    """
    Email Verification API
    """
    serializer = EmailVerificationSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            uidb64 = serializer.validated_data['uidb64']
            token = serializer.validated_data['token']
            
            unique_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=unique_id)
            
            if user and user_tokenizer_generate.check_token(user, token):
                user.is_active = True
                user.save()
                return Response({
                    'message': 'Email verification successful'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid verification link'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Invalid verification link'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def password_reset_request_api(request):
    """
    Password Reset Request API
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate password reset token
        current_site = get_current_site(request)
        subject = 'Password Reset Request'
        message = render_to_string('account/password/password-reset-email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        
        return Response({
            'message': 'Password reset email sent successfully'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def password_reset_confirm_api(request):
    """
    Password Reset Confirm API
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            uidb64 = serializer.validated_data['uidb64']
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            unique_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=unique_id)
            
            if user and default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({
                    'message': 'Password reset successful'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid reset link'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Invalid reset link'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_api(request):
    """
    Get current user profile
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)