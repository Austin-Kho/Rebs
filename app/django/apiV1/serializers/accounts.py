from rest_framework import serializers

from accounts.models import User, StaffAuth, Profile, Todo


# Accounts --------------------------------------------------------------------------
class StaffAuthInUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffAuth
        fields = ('pk', 'user', 'company', 'is_staff', 'assigned_project', 'allowed_projects',
                  'contract', 'payment', 'notice', 'project_cash', 'project_docs', 'project',
                  'company_cash', 'company_docs', 'human_resource', 'company_settings', 'auth_manage')


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        help_text='변경할 필요가 없으면 비워 두십시오.',
        style={'input_type': 'password', 'placeholder': '비밀번호'}
    )
    staffauth = StaffAuthInUserSerializer(read_only=True)
    profile = serializers.ReadOnlyField(source='profile.pk')

    class Meta:
        model = User
        fields = ('pk', 'email', 'username', 'is_active', 'is_superuser',
                  'date_joined', 'password', 'staffauth', 'profile')

    def save(self):
        instance = User(email=self.validated_data['email'],
                        username=self.validated_data['username'])
        password = self.validated_data['password']
        instance.set_password(password)
        instance.save()
        self.instance = instance
        return self.instance


class ProfileSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True, required=False)

    class Meta:
        model = Profile
        fields = ('pk', 'user', 'name', 'birth_date',
                  'cell_phone', 'image', 'like_post', 'like_comment')


class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ('pk', 'user', 'title', 'completed', 'soft_deleted')
