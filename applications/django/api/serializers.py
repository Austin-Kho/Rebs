from rest_framework import serializers

from accounts.models import User, StaffAuth, Profile, Todo
from company.models import Company, Department, Position, Staff
from project.models import (Project, UnitType, UnitFloorType,
                            ContractUnit, UnitNumber, ProjectBudget,
                            Site, SiteOwner, SiteOwnshipRelationship, SiteContract)
from rebs.models import (AccountSubD1, AccountSubD2, AccountSubD3,
                         ProjectAccountD1, ProjectAccountD2, WiseSaying)
from cash.models import (BankCode, CompanyBankAccount, ProjectBankAccount,
                         CashBook, ProjectCashBook, SalesPriceByGT,
                         InstallmentPaymentOrder, DownPayment, OverDueRule)
from contract.models import (OrderGroup, Contract, Contractor,
                             ContractorAddress, ContractorContact, ContractorRelease)
from notice.models import SalesBillIssue
from document.models import Group, Board, Category, LawsuitCase, Post, Image, Link, File, Comment, Tag


# Accounts --------------------------------------------------------------------------
class StaffAuthInUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffAuth
        fields = (
            'pk', 'company', 'is_staff', 'assigned_project', 'allowed_projects', 'contract', 'payment', 'notice',
            'project_cash',
            'project_docs',
            'project', 'company_cash', 'company_docs', 'human_resource', 'company_settings', 'auth_manage')


class ProfileInUserSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Profile
        fields = ('pk', 'url', 'user', 'name', 'birth_date', 'cell_phone', 'release_code')
        extra_kwargs = {'url': {'view_name': 'api:profile-detail'}}


class UserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='api:user-detail')
    password = serializers.CharField(
        write_only=True,
        required=True,
        help_text='변경할 필요가 없으면 비워 두십시오.',
        style={'input_type': 'password', 'placeholder': '비밀번호'}
    )
    staffauth = StaffAuthInUserSerializer()
    profile = ProfileInUserSerializer()

    class Meta:
        model = User
        fields = (
            'pk', 'url', 'email', 'username', 'is_active',
            'is_superuser', 'date_joined', 'password',
            'staffauth', 'profile')

    def save(self):
        instance = User(email=self.validated_data['email'],
                        username=self.validated_data['username'])
        password = self.validated_data['password']
        instance.set_password(password)
        instance.save()
        self.instance = instance
        return self.instance


class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ('pk', 'user', 'title', 'completed', 'created_at', 'updated_at', 'soft_deleted')


# Company --------------------------------------------------------------------------
class DepartsInCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('pk', 'upper_depart', 'name', 'task')


class PositionsInCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ('pk', 'rank', 'title', 'description')


class CompanySerializer(serializers.ModelSerializer):
    departments = DepartsInCompanySerializer(many=True, read_only=True)
    positions = PositionsInCompanySerializer(many=True, read_only=True)

    class Meta:
        model = Company
        fields = ('pk', 'name', 'ceo', 'tax_number', 'org_number',
                  'business_cond', 'business_even', 'es_date', 'op_date', 'zipcode',
                  'address1', 'address2', 'address3', 'departments', 'positions')


class StaffsInDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ('pk', 'position', 'name')


class DepartmentSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    staffs = StaffsInDepartmentSerializer(many=True, read_only=True)

    class Meta:
        model = Department
        fields = ('pk', 'company', 'name', 'task', 'staffs')


class PositionSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')

    class Meta:
        model = Position
        fields = ('pk', 'rank', 'title', 'description')


class StaffSerializer(serializers.ModelSerializer):
    department = serializers.SlugRelatedField(queryset=Department.objects.all(), slug_field='name')
    gender = serializers.ChoiceField(choices=Staff.GENDER_CHOICES)
    gender_desc = serializers.CharField(source='get_gender_display', read_only=True)
    status = serializers.ChoiceField(choices=Staff.STATUS_CHOICES)
    status_desc = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Staff
        fields = ('pk', 'department', 'position', 'name', 'birth_date', 'gender', 'gender_desc',
                  'entered_date', 'personal_phone', 'email', 'status', 'status_desc')


# Project --------------------------------------------------------------------------
class ProjectSerializer(serializers.ModelSerializer):
    kind = serializers.ChoiceField(choices=Project.KIND_CHOICES)
    kind_desc = serializers.CharField(source='get_kind_display', read_only=True)

    class Meta:
        model = Project
        fields = ('pk', 'company', 'name', 'order', 'kind', 'kind_desc', 'start_year',
                  'is_direct_manage', 'is_returned_area', 'is_unit_set',
                  'local_zipcode', 'local_address1', 'local_address2', 'local_address3',
                  'area_usage', 'build_size', 'num_unit', 'buy_land_extent', 'scheme_land_extent',
                  'donation_land_extent', 'on_floor_area', 'under_floor_area', 'total_floor_area',
                  'build_area', 'floor_area_ratio', 'build_to_land_ratio',
                  'num_legal_parking', 'num_planed_parking')


class UnitTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitType
        fields = (
            'pk', 'project', 'name', 'color', 'actual_area',
            'supply_area', 'contract_area', 'average_price', 'num_unit')


class UnitFloorTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitFloorType
        fields = ('pk', 'project', 'start_floor', 'end_floor', 'extra_cond', 'alias_name')


class UnitNumberSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(queryset=Project.objects.all(), slug_field='name')
    floor_type = serializers.SlugRelatedField(queryset=UnitFloorType.objects.all(), slug_field='alias_name')

    class Meta:
        model = UnitNumber
        fields = ('pk', 'project', 'floor_type', 'bldg_no', 'bldg_unit_no',
                  'contract_unit', 'bldg_line', 'floor_no', 'is_hold', 'hold_reason')


class ContractUnitSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(queryset=Project.objects.all(), slug_field='name')
    unit_type = serializers.SlugRelatedField(queryset=UnitType.objects.all(), slug_field='name')
    unitnumber = UnitNumberSerializer()

    class Meta:
        model = ContractUnit
        fields = ('pk', 'project', 'unit_type', 'unit_code', 'unitnumber', 'contract')


class ProjectBudgetSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(queryset=Project.objects.all(), slug_field='name')
    account_d1 = serializers.SlugRelatedField(queryset=ProjectAccountD1.objects.all(), slug_field='name')
    account_d2 = serializers.SlugRelatedField(queryset=ProjectAccountD2.objects.all(), slug_field='name')

    class Meta:
        model = ProjectBudget
        fields = ('pk', 'project', 'account_d1', 'account_d2', 'budget')


class SiteSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(queryset=Project.objects.all(), slug_field='name')

    class Meta:
        model = Site
        fields = ('pk', 'project', 'order', 'district', 'lot_number', 'site_purpose',
                  'official_area', 'returned_area', 'rights_restrictions', 'dup_issue_date')


class SiteOwnerSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(queryset=Project.objects.all(), slug_field='name')
    own_sort_desc = serializers.CharField(source='get_own_sort_display', read_only=True)

    class Meta:
        model = SiteOwner
        fields = ('pk', 'project', 'owner', 'date_of_birth', 'phone1', 'phone2',
                  'zipcode', 'address1', 'address2', 'address3', 'own_sort', 'own_sort_desc',
                  'sites', 'counsel_record', 'user')


class SiteOwnshipRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteOwnshipRelationship
        fields = ('pk', 'site', 'site_owner', 'ownership_ratio', 'owned_area', 'acquisition_date')


class SiteContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteContract
        fields = ('pk', 'project', 'owner', 'contract_date', 'total_price', 'down_pay1', 'down_pay1_is_paid',
                  'down_pay2', 'down_pay2_date', 'down_pay2_is_paid', 'inter_pay1', 'inter_pay1_date',
                  'inter_pay1_is_paid',
                  'inter_pay2', 'inter_pay2_date', 'inter_pay2_is_paid', 'remain_pay', 'remain_pay_date',
                  'remain_pay_is_paid',
                  'ownership_completion', 'acc_bank', 'acc_number', 'acc_owner', 'note')


class InlineAccSubD1Serializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSubD1
        fields = ('pk', 'name')


class InlineAccSubD2Serializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSubD2
        fields = ('pk', 'name')


class InlineAccSubD3Serializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSubD3
        fields = ('pk', 'name')


class AccountSubD1Serializer(serializers.ModelSerializer):
    acc_d2s = InlineAccSubD2Serializer(many=True, read_only=True)

    class Meta:
        model = AccountSubD1
        fields = ('pk', 'code', 'name', 'description', 'acc_d2s')


class AccountSubD2Serializer(serializers.ModelSerializer):
    d1 = InlineAccSubD1Serializer(read_only=True)
    acc_d3s = InlineAccSubD3Serializer(many=True, read_only=True)

    class Meta:
        model = AccountSubD2
        fields = ('pk', 'd1', 'code', 'name', 'description', 'acc_d3s')


class AccountSubD3Serializer(serializers.ModelSerializer):
    d2 = InlineAccSubD2Serializer(read_only=True)

    class Meta:
        model = AccountSubD3
        fields = ('pk', 'd2', 'code', 'name', 'is_special', 'description')


class InlineProjectAccD1Serializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAccountD1
        fields = ('pk', 'name')


class InlineProjectAccD2Serializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAccountD2
        fields = ('pk', 'name')


class ProjectAccountD1Serializer(serializers.ModelSerializer):
    acc_d2s = InlineProjectAccD2Serializer(many=True, read_only=True)
    sort_desc = serializers.CharField(source='get_sort_display', read_only=True)

    class Meta:
        model = ProjectAccountD1
        fields = ('pk', 'sort', 'sort_desc', 'code', 'name', 'description', 'acc_d2s')


class ProjectAccountD2Serializer(serializers.ModelSerializer):
    d1 = InlineProjectAccD1Serializer(read_only=True)

    class Meta:
        model = ProjectAccountD2
        fields = ('pk', 'd1', 'code', 'sub_title', 'name', 'description')


class BankCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankCode
        fields = ('pk', 'code', 'name')


class CompanyBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyBankAccount
        fields = ('pk', 'company', 'division', 'bankcode', 'alias_name', 'number',
                  'holder', 'open_date', 'note', 'inactive')


class CashBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashBook
        fields = ('pk', 'company', 'cash_category1', 'cash_category2', 'account',
                  'content', 'trader', 'bank_account', 'income', 'outlay', 'evidence',
                  'note', 'deal_date', 'user', 'created_at', 'updated_at')


class ProjectBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectBankAccount
        fields = ('pk', 'project', 'bankcode', 'alias_name', 'number',
                  'holder', 'open_date', 'note', 'inactive', 'directpay')


class ProjectCashBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCashBook
        fields = ('pk', 'project', 'cash_category1', 'project_account_d1', 'project_account_d2',
                  'is_record_separate', 'is_contract_payment', 'contract', 'installment_order', 'is_release',
                  'is_refund_contractor', 'content', 'trader', 'bank_account', 'income', 'outlay', 'evidence',
                  'note', 'deal_date', 'user', 'created_at', 'updated_at')


class SalesPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesPriceByGT
        fields = ('pk', 'project', 'order_group', 'unit_type', 'unit_floor_type',
                  'price_build', 'price_land', 'price_tax', 'price')


class InstallmentOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstallmentPaymentOrder
        fields = ('pk', 'project', 'pay_sort', 'pay_code', 'pay_time',
                  'pay_name', 'alias_name', 'is_pm_cost', 'pay_due_date', 'extra_due_date')


class DownPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DownPayment
        fields = ('pk', 'project', 'order_group', 'unit_type', 'number_payments', 'payment_amount')


class OverDueRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = OverDueRule
        fields = ('pk', 'project', 'term_start', 'term_end', 'rate_year')


class OrderGroupSerializer(serializers.ModelSerializer):
    sort_desc = serializers.CharField(source='get_sort_display', read_only=True)

    class Meta:
        model = OrderGroup
        fields = ('pk', 'project', 'order_number', 'sort', 'sort_desc', 'order_group_name')


# Contract --------------------------------------------------------------------------
class ContractorAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorAddress
        fields = ('pk', 'contractor', 'id_zipcode', 'id_address1', 'id_address2', 'id_address3',
                  'dm_zipcode', 'dm_address1', 'dm_address2', 'dm_address3')


class ContractorContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorContact
        fields = ('pk', 'contractor', 'cell_phone', 'home_phone', 'other_phone', 'email')


class ContractorSerializer(serializers.ModelSerializer):
    contractoraddress = ContractorAddressSerializer()
    contractorcontact = ContractorContactSerializer()

    class Meta:
        model = Contractor
        fields = (
            'pk', 'contract', 'name', 'birth_date', 'gender', 'contractoraddress', 'contractorcontact',
            'is_registed', 'status', 'reservation_date', 'contract_date', 'note')


class ContractSerializer(serializers.ModelSerializer):
    contractunit = ContractUnitSerializer()
    contractor = ContractorSerializer()

    class Meta:
        model = Contract
        fields = (
            'pk', 'project', 'order_group', 'serial_number', 'activation', 'contractunit', 'contractor', 'user')


class ContractorReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorRelease
        fields = ('pk', 'project', 'contractor', 'status', 'refund_amount',
                  'refund_account_bank', 'refund_account_number', 'refund_account_depositor',
                  'request_date', 'completion_date', 'note', 'user', 'created_at', 'updated_at')


class SallesBillIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesBillIssue
        fields = ('pk', 'project', 'now_payment_order', 'host_name', 'host_tel',
                  'agency', 'agency_tel', 'bank_account1', 'bank_number1', 'bank_host1',
                  'bank_account2', 'bank_number2', 'bank_host2', 'zipcode', 'address1', 'address2', 'address3',
                  'title', 'content', 'user', 'updated_at')


# Document --------------------------------------------------------------------------
class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('pk', 'name', 'manager')


class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ('pk', 'group', 'name', 'order', 'search_able', 'manager')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('pk', 'board', 'name', 'parent', 'order')


class LawSuitCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = LawsuitCase
        fields = ('pk', 'project', 'sort', 'level', 'related_case', 'court',
                  'other_agency', 'case_number', 'case_name', 'plaintiff', 'defendant',
                  'related_debtor', 'case_start_date', 'summary', 'user', 'created', 'updated')


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('pk', 'board', 'is_notice', 'project', 'category', 'lawsuit',
                  'title', 'execution_date', 'content', 'is_hide_comment', 'hit', 'like',
                  'dislike', 'blame', 'ip', 'device', 'secret', 'password', 'user', 'soft_delete', 'created', 'updated')


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('pk', 'post', 'image', 'created')


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ('pk', 'post', 'link', 'hit')


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('pk', 'post', 'file', 'hit')


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            'pk', 'post', 'content', 'like', 'dislike', 'blame', 'ip', 'device', 'secret', 'password', 'user',
            'soft_delete', 'created', 'updated')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('pk', 'board', 'tag', 'post')


class WiseSaySerializer(serializers.ModelSerializer):
    class Meta:
        model = WiseSaying
        fields = ('pk', 'saying_ko', 'saying_en', 'spoked_by')
