import base64

from allauth.account.forms import default_token_generator
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.models import User, StaffAuth, Profile, Todo, PasswordResetToken
from ..pagination import *
from ..permission import *
from ..serializers.accounts import *


# Accounts --------------------------------------------------------------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPaginationThreeThousand
    permission_classes = (permissions.AllowAny,)
    filterset_fields = ('is_staff', 'is_active',)


class StaffAuthViewSet(viewsets.ModelViewSet):
    queryset = StaffAuth.objects.all()
    serializer_class = StaffAuthInUserSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOnly)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DocScrapeViewSet(viewsets.ModelViewSet):
    queryset = DocScrape.objects.all()
    serializer_class = DocScrapeSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOnly)
    filterset_fields = ('user',)
    search_fields = ('title', 'post__title', 'post__content')


# class PostScrapeViewSet(viewsets.ModelViewSet):
#     queryset = PostScrape.objects.all()
#     serializer_class = PostScrapeSerializer
#     permission_classes = (permissions.IsAuthenticated, IsOwnerOnly)
#     filterset_fields = ('user',)
#     search_fields = ('title', 'post__title', 'post__content')


class TodoViewSet(viewsets.ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsOwnerOnly)
    filterset_fields = ('user', 'soft_deleted')
    search_fields = ('title',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CheckPasswordView(APIView):
    """비밀번호가 맞는지 체크하는 API"""
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        password = request.data.get('password', None)

        if not password:
            return Response({'detail': 'Password not provided.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(email=request.data.get('email'), password=password)

        if user is not None:
            # Password is correct
            return Response({'detail': 'Password correct.'}, status=status.HTTP_200_OK)
        else:
            # Password is correct
            return Response({'detail': 'Password incorrect.'}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """종전 비밀번호를 확인 한 후 비밀번호를 변경하는 API"""
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            # Check if the old password is correct
            old_password = serializer.validated_data.get('old_password')
            if not check_password(old_password, request.user.password):
                return Response({'detail': '패스워드를 맞지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

            # Update the password
            new_password = serializer.validated_data.get('new_password')
            request.user.set_password(new_password)
            request.user.save()

            # Update the user's session to prevent the user from being logged out
            update_session_auth_hash(request, request.user)

            return Response({'detail': '패스워드가 변경되었습니다.'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """비밀번호 분실 시 재설정 링크를 요청하는 API"""
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request, *args, **kwargs):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            # Find the user with the given email
            email = serializer.validated_data.get('email')
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'detail': '입력한 이메일로 등록된 사용자가 존재하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

            # Generate a password reset token
            token = default_token_generator.make_token(user)
            try:
                token_db = PasswordResetToken.objects.get(user=user)
                token_db.token = token
            except PasswordResetToken.DoesNotExist:
                token_db = PasswordResetToken(user=user, token=token)
            token_db.save()

            # Create a password reset link
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

            scheme = 'http' if settings.DEBUG else 'https'
            reset_link = f'{scheme}://{request.get_host()}/#/accounts/pass-reset/?uidb64={uidb64}&token={token}'

            # Send the password reset email
            subject = f'[Rebs] {user.username}님 계정 비밀번호 초기화 링크 안내드립니다.'
            message = f'비밀번호를 재설정 하기 위해서 다음 링크를 클릭 하세요.: \n{reset_link}\n\n이 링크는 발송 후 10분간 만 유효합니다.'
            send_mail(subject, message, settings.EMAIL_DEFAULT_SENDER, [email])

            return Response({'detail': '비밀번호 재설정을 위한 이메일을 발송했습니다.'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """비밀번호 재설정 링크를 통해서 비밀번호를 재설정하는 API"""
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        while len(user_id) % 4 != 0:
            user_id += '='
        user_id = base64.b64decode(user_id, validate=True).decode('utf-8')
        token = kwargs.get('token')

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            token_db = PasswordResetToken.objects.get(user=user)
            if not token_db.is_expired():
                # Token is valid, perform password reset
                new_password = request.data.get('new_password')
                user.set_password(new_password)
                user.save()

                # # Log the user in with the new password
                # authenticated_user = authenticate(username=user.username, password=new_password)
                # login(request, authenticated_user)

                return Response({'detail': 'Password reset successful'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'This token was expired'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'detail': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)


class PasswordResetTokenViewSet(viewsets.ModelViewSet):
    queryset = PasswordResetToken.objects.all()
    serializer_class = PasswordResetTokenSerializer
    permission_classes = (permissions.AllowAny,)
    filterset_fields = ('user', 'token')
