import hashlib
from datetime import datetime

from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager, PermissionsMixin

from django.contrib.auth.validators import UnicodeUsernameValidator

from document.models import Post, Comment


class User(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    Username and password are required. Other fields are optional.
    """
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    email = models.EmailField(_('email address'), max_length=255, unique=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ('-date_joined',)

    def __str__(self):
        return self.username

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)


class StaffAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company = models.ForeignKey('company.Company', on_delete=models.PROTECT, verbose_name='회사정보')
    is_staff = models.BooleanField('본사 관리자', default=False, help_text='외부 관계자가 아닌 본사 직원(관리자)일 경우 선택')
    is_project_staff = models.BooleanField('프로젝트 관리자', default=False, help_text='본사 직원 외 프로젝트 관리 직원(관리자)일 경우 선택')
    allowed_projects = models.ManyToManyField('project.Project', related_name='allowed_projects',
                                              blank=True, verbose_name='허용 프로젝트',
                                              help_text='사용자가 조회 및 관리할 수 있는 프로젝트들을 선택합니다.')
    assigned_project = models.ForeignKey('project.Project',
                                         on_delete=models.SET_NULL, null=True,
                                         blank=True, verbose_name='담당 메인 프로젝트',
                                         help_text='선택한 프로젝트를 사용자의 각 화면에서 기본 프로젝트로 보여줍니다.')
    AUTH_CHOICE = (('0', '권한없음'), ('1', '읽기권한'), ('2', '쓰기권한'))
    contract = models.CharField('분양 계약 관리', max_length=1, choices=AUTH_CHOICE, default='0')
    payment = models.CharField('분양 수납 관리', max_length=1, choices=AUTH_CHOICE, default='0')
    notice = models.CharField('고객 고지 관리', max_length=1, choices=AUTH_CHOICE, default='0')
    project_cash = models.CharField('현장 자금 관리', max_length=1, choices=AUTH_CHOICE, default='0')
    project_docs = models.CharField('현장 문서 관리', max_length=1, choices=AUTH_CHOICE, default='0')
    project = models.CharField('신규 프로젝트', max_length=1, choices=AUTH_CHOICE, default='0')
    company_cash = models.CharField('본사 자금 관리', max_length=1, choices=AUTH_CHOICE, default='0')
    company_docs = models.CharField('본사 문서 관리', max_length=1, choices=AUTH_CHOICE, default='0')
    human_resource = models.CharField('본사 인사 관리', max_length=1, choices=AUTH_CHOICE, default='0')
    company_settings = models.CharField('회사 관련설정', max_length=1, choices=AUTH_CHOICE, default='0')
    auth_manage = models.CharField('권한 설정 관리', max_length=1, choices=AUTH_CHOICE, default='0')

    def __str__(self):
        return f'{self.user} :: 권한'

    class Meta:
        ordering = ('-id',)
        verbose_name = '스태프 권한'
        verbose_name_plural = '스태프 권한'


def get_image_filename(instance, filename):
    year = datetime.today().strftime('%Y')
    month = datetime.today().strftime('%m')
    username = instance.user
    hash_value = hashlib.blake2b(digest_size=3).hexdigest()
    return f"users/{year}/{month}/{username}_{hash_value}_{filename}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField('성명', max_length=20, blank=True)
    birth_date = models.DateField('생년월일', null=True, blank=True)
    cell_phone = models.CharField('휴대폰', max_length=13, blank=True)
    image = models.ImageField(upload_to=get_image_filename, null=True, blank=True, verbose_name='프로필 이미지')
    like_posts = models.ManyToManyField(Post, blank=True, related_name='post_like_users')
    like_comments = models.ManyToManyField(Comment, blank=True, related_name='comment_like_users')
    blame_posts = models.ManyToManyField(Post, blank=True, related_name='post_blame_users')
    blame_comments = models.ManyToManyField(Comment, blank=True, related_name='comment_blame_users')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-id',)
        verbose_name = '사용자 프로필'
        verbose_name_plural = '사용자 프로필'


class Scrape(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    title = models.CharField('스크랩 타이틀', max_length=50, blank=True, default='')
    created = models.DateTimeField('보관일', auto_now_add=True)

    def __str__(self):
        return self.title if self.title else self.post.title

    class Meta:
        verbose_name = '스크랩'
        verbose_name_plural = '스크랩'


class Todo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todos')
    title = models.CharField('할일내용', max_length=50)
    completed = models.BooleanField('완료여부', default=False)
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    soft_deleted = models.BooleanField('삭제여부', default=False)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('id',)


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='users')
    token = models.CharField('토큰', max_length=255)
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('수정일시', auto_now=True)

    def is_expired(self):
        # Check if 10 minutes have passed since the last update
        time_diff = timezone.now() - self.updated
        return time_diff.total_seconds() >= 600
