from django.db import transaction
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist

from cash.models import ProjectBankAccount, ProjectCashBook
from project.models import Project, ProjectIncBudget
from items.models import UnitType, HouseUnit, KeyUnit
from payment.models import SalesPriceByGT, InstallmentPaymentOrder, DownPayment
from rebs.models import AccountSort, ProjectAccountD2, ProjectAccountD3
from contract.models import (OrderGroup, Contract, ContractPrice, Contractor,
                             ContractorAddress, ContractorContact,
                             Succession, ContractorRelease, ContractFile)

from .items import SimpleUnitTypeSerializer
from .payment import SimpleInstallmentOrderSerializer, SimpleOrderGroupSerializer


# Contract --------------------------------------------------------------------------
class OrderGroupSerializer(serializers.ModelSerializer):
    sort_desc = serializers.CharField(source='get_sort_display', read_only=True)

    class Meta:
        model = OrderGroup
        fields = ('pk', 'project', 'order_number', 'sort', 'sort_desc', 'order_group_name')


class HouseUnitInKeyUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = HouseUnit
        fields = ('pk', '__str__', 'floor_type')


class KeyUnitInContractSerializer(serializers.ModelSerializer):
    houseunit = HouseUnitInKeyUnitSerializer()

    class Meta:
        model = KeyUnit
        fields = ('pk', 'unit_code', 'houseunit')


class AddressInContractorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorAddress
        fields = ('pk', 'id_zipcode', 'id_address1', 'id_address2', 'id_address3',
                  'dm_zipcode', 'dm_address1', 'dm_address2', 'dm_address3')


class ContactInContractorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorContact
        fields = ('pk', 'cell_phone', 'home_phone', 'other_phone', 'email')


class ContPriceInContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractPrice
        fields = ('pk', 'price', 'price_build', 'price_land',
                  'price_tax', 'down_pay', 'middle_pay', 'remain_pay')


class ContractorInContractSerializer(serializers.ModelSerializer):
    qualifi_display = serializers.CharField(source='get_qualification_display', read_only=True)
    contractoraddress = AddressInContractorSerializer()
    contractorcontact = ContactInContractorSerializer()

    class Meta:
        model = Contractor
        fields = ('pk', 'name', 'birth_date', 'gender', 'qualification', 'qualifi_display',
                  'contractoraddress', 'contractorcontact', 'status',
                  'reservation_date', 'contract_date', 'is_active', 'note')


def get_cont_price(instance, houseunit=None):
    try:
        price = ProjectIncBudget.objects.get(project=instance.project,
                                             order_group=instance.order_group,
                                             unit_type=instance.unit_type).average_price
    except ProjectIncBudget.DoesNotExist:
        price = UnitType.objects.get(pk=instance.unit_type).average_price
    except UnitType.DoesNotExist:
        price = 0

    price_build = None
    price_land = None
    price_tax = None

    if houseunit:
        try:
            sales_price = SalesPriceByGT.objects.get(order_group=instance.order_group,
                                                     unit_type=instance.unit_type,
                                                     unit_floor_type=houseunit.floor_type)
            price = sales_price.price
            price_build = sales_price.price_build
            price_land = sales_price.price_land
            price_tax = sales_price.price_tax
        except SalesPriceByGT.DoesNotExist:
            pass

    return price, price_build, price_land, price_tax


def get_pay_amount(instance, price):
    # ### 회차 데이터
    install_order = InstallmentPaymentOrder.objects.filter(project=instance.project)

    downs = install_order.filter(pay_sort='1')  # 계약금 분류 회차 리스트
    middles = install_order.filter(pay_sort='2')  # 중도금 분류 회차 리스트
    remains = install_order.filter(pay_sort='3')  # 잔금 분류 회차 리스트

    down_num = len(downs.distinct().values_list('pay_code'))  # 계약금 분납 회수
    middle_num = len(middles.distinct().values_list('pay_code'))  # 중도금 분납 회수
    remain_num = len(remains.distinct().values_list('pay_code'))  # 잔금 분납 회수

    down_ratio = downs.first().pay_ratio / 100 if downs.first().pay_ratio else 0.1  # 회차별 계약금 비율(기본값 10%)
    middle_ratio = middles.first().pay_ratio / 100 if middles.first().pay_ratio else 0.1  # 회차별 중도금 비율(기본값 10%)

    try:
        down_data = DownPayment.objects.get(order_group=instance.order_group,
                                            unit_type=instance.unit_type)  # 현재 차수 및 타입의 계약금 데이터
        down = down_data.payment_amount  # 계약금 데이터가 있으면 해당 데이터가 회차별 계약금 금액
    except DownPayment.DoesNotExist:
        down = price * down_ratio  # 계약금 데이터 없을 경우 회차별 계약금 금액
    remain = (price - (price * middle_ratio * middle_num) - (down * down_num)) / remain_num  # 계약금/중도금 공제 잔금액

    middle = price * middle_ratio
    return down, middle, remain


class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ('pk', 'project', 'order_group', 'unit_type', 'serial_number', 'activation')

    @transaction.atomic
    def update(self, instance, validated_data):
        # instance.__dict__.update(**validated_data)
        # instance.save()
        contracts = Contract.objects.filter(project=instance.project, activation=True)

        for contract in contracts:
            try:
                house_unit = contract.keyunit.houseunit
            except ObjectDoesNotExist:
                house_unit = None
            price = get_cont_price(contract, house_unit)
            pay_amount = get_pay_amount(contract, price[0])

            try:  # 계약가격 정보 존재 여부 확인
                cont_price = contract.contractprice
            except ContractPrice.DoesNotExist:
                cont_price = None

            if cont_price:  # 계약가격 데이터가 존재하는 경우
                # 계약 가격 정보 업데이트
                cont_price.price = price[0]
                cont_price.price_build = price[1]
                cont_price.price_land = price[2]
                cont_price.price_tax = price[3]
                cont_price.down_pay = pay_amount[0]
                cont_price.middle_pay = pay_amount[1]
                cont_price.remain_pay = pay_amount[2]
                cont_price.save()

            else:  # 계약가격 데이터가 존재하지 않는 경우 계약 가격 정보 생성
                cont_price = ContractPrice(contract=contract,
                                           price=price[0],
                                           price_build=price[1],
                                           price_land=price[2],
                                           price_tax=price[3],
                                           down_pay=pay_amount[0],
                                           middle_pay=pay_amount[1],
                                           remain_pay=pay_amount[2])
                cont_price.save()

        return instance


class ProjectCashBookInContractSerializer(serializers.ModelSerializer):
    installment_order = SimpleInstallmentOrderSerializer()

    class Meta:
        model = ProjectCashBook
        fields = ('pk', 'deal_date', 'income', 'bank_account', 'trader', 'installment_order')


class ProjectCashBookOrderInContractSerializer(serializers.ModelSerializer):
    installment_order = SimpleInstallmentOrderSerializer()

    class Meta:
        model = ProjectCashBook
        fields = ('installment_order',)


class ProjectCashBookIncsInContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCashBook
        fields = ('income',)


class ContractFileInContractSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractFile
        fields = ('pk', 'file', 'file_name', 'file_size', 'created', 'user')


class ContractSetSerializer(serializers.ModelSerializer):
    order_group_sort = serializers.SerializerMethodField(read_only=True)
    keyunit = KeyUnitInContractSerializer(read_only=True)
    contractprice = ContPriceInContractSerializer(read_only=True)
    contractor = ContractorInContractSerializer(read_only=True)
    payments = serializers.SerializerMethodField(read_only=True)
    last_paid_order = serializers.SerializerMethodField(read_only=True)
    total_paid = serializers.SerializerMethodField(read_only=True)
    order_group_desc = SimpleOrderGroupSerializer(source='order_group', read_only=True)
    unit_type_desc = SimpleUnitTypeSerializer(source='unit_type', read_only=True)
    contract_files = ContractFileInContractSetSerializer(many=True, read_only=True)

    class Meta:
        model = Contract
        fields = ('pk', 'project', 'order_group_sort', 'order_group', 'unit_type', 'serial_number',
                  'activation', 'is_sup_cont', 'sup_cont_date', 'keyunit', 'contractprice', 'contractor',
                  'payments', 'last_paid_order', 'total_paid', 'order_group_desc', 'unit_type_desc', 'contract_files')

    @staticmethod
    def get_order_group_sort(obj):
        return obj.order_group.sort

    @staticmethod
    def get_payment_list(instance):
        return instance.payments.filter(project_account_d3__in=(1, 4))

    def get_payments(self, instance):
        payments = self.get_payment_list(instance).order_by('deal_date', 'id')
        return ProjectCashBookInContractSerializer(payments, many=True, read_only=True).data

    def get_last_paid_order(self, instance):
        due_amt = 0
        order_data = {}
        install_order = InstallmentPaymentOrder.objects.filter(project=instance.project)

        total_paid = self.get_total_paid(instance)
        price = get_cont_price(instance)
        amount = get_pay_amount(instance, price[0])

        for order in install_order:
            due_amt += amount[int(order.pay_sort) - 1]
            if total_paid >= due_amt:
                project_cash = ProjectCashBook.objects.filter(installment_order=order).first()
                order_data = ProjectCashBookOrderInContractSerializer(project_cash, read_only=True).data
            else:
                break

        return order_data.get('installment_order') if order_data else None

    def get_total_paid(self, instance):
        inc_data = ProjectCashBookIncsInContractSerializer(self.get_payment_list(instance),
                                                           many=True,
                                                           read_only=True).data
        return sum([i.get('income') for i in inc_data])

    @transaction.atomic
    def create(self, validated_data):
        # 1. 계약정보 테이블 입력
        contract = Contract.objects.create(**validated_data)
        contract.save()

        # 2. 계약 유닛 연결
        keyunit_data = self.initial_data.get('keyunit')
        keyunit = KeyUnit.objects.get(pk=keyunit_data)
        keyunit.contract = contract
        keyunit.save()

        # 분양가격 설정 데이터 불러오기
        price = get_cont_price(contract)
        pay_amount = get_pay_amount(contract, price[0])

        # 3. 동호수 연결
        if self.initial_data.get('houseunit'):
            house_unit_data = self.initial_data.get('houseunit')
            house_unit = HouseUnit.objects.get(pk=house_unit_data)
            house_unit.key_unit = keyunit
            house_unit.save()

            # 분양가격 설정 데이터 불러오기
            price = get_cont_price(contract, house_unit)
            pay_amount = get_pay_amount(contract, price[0])

        # 4. 계약 가격 정보 등록
        cont_price = ContractPrice(contract=contract,
                                   price=price[0],
                                   price_build=price[1],
                                   price_land=price[2],
                                   price_tax=price[3],
                                   down_pay=pay_amount[0],
                                   middle_pay=pay_amount[1],
                                   remain_pay=pay_amount[2])
        cont_price.save()

        # 5. 계약자 정보 테이블 입력
        contractor_name = self.initial_data.get('name')
        birth_date = self.initial_data.get('birth_date', None)
        contractor_gender = self.initial_data.get('gender')
        qualification = self.initial_data.get('qualification', None)
        contractor_status = self.initial_data.get('status')
        reservation_date = self.initial_data.get('reservation_date', None)
        contract_date = self.initial_data.get('contract_date', None)
        contractor_note = self.initial_data.get('note')

        contractor = Contractor.objects.create(contract=contract,
                                               name=contractor_name,
                                               birth_date=birth_date if birth_date else None,
                                               gender=contractor_gender,
                                               qualification=qualification if qualification else '1',
                                               status=contractor_status,
                                               reservation_date=reservation_date if reservation_date else None,
                                               contract_date=contract_date if contract_date else None,
                                               note=contractor_note)
        contractor.save()

        # 6. 계약자 주소 테이블 입력
        address_id_zipcode = self.initial_data.get('id_zipcode')
        address_id_address1 = self.initial_data.get('id_address1')
        address_id_address2 = self.initial_data.get('id_address2')
        address_id_address3 = self.initial_data.get('id_address3')
        address_dm_zipcode = self.initial_data.get('dm_zipcode')
        address_dm_address1 = self.initial_data.get('dm_address1')
        address_dm_address2 = self.initial_data.get('dm_address2')
        address_dm_address3 = self.initial_data.get('dm_address3')

        contractor_address = ContractorAddress.objects.create(contractor=contractor,
                                                              id_zipcode=address_id_zipcode,
                                                              id_address1=address_id_address1,
                                                              id_address2=address_id_address2,
                                                              id_address3=address_id_address3,
                                                              dm_zipcode=address_dm_zipcode,
                                                              dm_address1=address_dm_address1,
                                                              dm_address2=address_dm_address2,
                                                              dm_address3=address_dm_address3)
        contractor_address.save()

        # 7. 계약자 연락처 테이블 입력
        contact_cell_phone = self.initial_data.get('cell_phone')
        contact_home_phone = self.initial_data.get('home_phone')
        contact_other_phone = self.initial_data.get('other_phone')
        contact_email = self.initial_data.get('email')

        contractor_contact = ContractorContact.objects.create(contractor=contractor,
                                                              cell_phone=contact_cell_phone,
                                                              home_phone=contact_home_phone,
                                                              other_phone=contact_other_phone,
                                                              email=contact_email)
        contractor_contact.save()

        # 8. 계약금 -- 수납 정보 테이블 입력
        if self.initial_data.get('deal_date'):
            project = self.initial_data.get('project')
            payment_project = Project.objects.get(pk=project)
            order_group_sort = int(self.initial_data.get('order_group_sort'))
            payment_account_d2 = ProjectAccountD2.objects.get(pk=order_group_sort)
            acc_d3 = 1 if order_group_sort == 1 else 4  # 분담금일 경우 1, 분양대금일 경우 4
            payment_account_d3 = ProjectAccountD3.objects.get(pk=acc_d3)
            ins_order = self.initial_data.get('installment_order')
            payment_installment_order = InstallmentPaymentOrder.objects.get(pk=ins_order)
            payment_serial_number = self.initial_data.get('serial_number')
            payment_trader = self.initial_data.get('trader')
            bank_account = self.initial_data.get('bank_account')
            payment_bank_account = ProjectBankAccount.objects.get(pk=bank_account)
            payment_income = self.initial_data.get('income')
            payment_deal_date = self.initial_data.get('deal_date')

            down_payment = ProjectCashBook.objects.create(project=payment_project,
                                                          sort=AccountSort.objects.get(pk=1),
                                                          project_account_d2=payment_account_d2,
                                                          project_account_d3=payment_account_d3,
                                                          contract=contract,
                                                          installment_order=payment_installment_order,
                                                          content=f'{contractor_name}[{payment_serial_number}] 대금납부',
                                                          trader=payment_trader,
                                                          bank_account=payment_bank_account,
                                                          income=payment_income,
                                                          deal_date=payment_deal_date)
            down_payment.save()

        return contract

    @transaction.atomic
    def update(self, instance, validated_data):
        # 1. 계약정보 테이블 입력
        instance.__dict__.update(**validated_data)
        instance.order_group = validated_data.get('order_group', instance.order_group)
        instance.unit_type = validated_data.get('unit_type', instance.unit_type)
        instance.save()

        # 1-2. 동호수 변경 여부 확인 및 변경 사항 적용
        keyunit_pk = self.initial_data.get('keyunit')  # keyunit => pk
        houseunit_pk = self.initial_data.get('houseunit')  # house_unit => pk

        keyunit = KeyUnit.objects.get(pk=keyunit_pk)
        house_unit = HouseUnit.objects.get(pk=houseunit_pk) if houseunit_pk else None

        same_unit_exist = False  # 동호가 있고 수정되지 않았는지 여부

        if instance.keyunit.pk != keyunit_pk:  # 계약유닛(keyunit)이 수정된 경우
            try:  # 종전 동호수가 있는 경우
                old_houseunit = instance.keyunit.houseunit
                if old_houseunit != houseunit_pk:  # 동호수가 수정된 경우
                    old_houseunit.key_unit = None  # 해당 동호수를 삭제
                    old_houseunit.save()
                else:
                    same_unit_exist = True
            except ObjectDoesNotExist:  # 종전 동호수가 없는 경우
                pass

            # 2. 계약 유닛 연결
            old_keyunit = instance.keyunit
            old_keyunit.contract = None  # 종전 계약의 계약유닛 삭제
            old_keyunit.save()
            keyunit.contract = instance  # 현재 계약건과 변경 유닛을 연결
            keyunit.save()

            # 3. 동호수 연결
            if houseunit_pk:
                house_unit.key_unit = keyunit  # 동호수를 계약유닛과 연결
                house_unit.save()
        else:  # 계약유닛(keyunit)이 수정되지 않은 경우
            try:  # 종전 동호수가 있는 경우
                old_houseunit = instance.keyunit.houseunit
                if old_houseunit != houseunit_pk:  # 동호수가 수정된 경우
                    old_houseunit.key_unit = None  # 먼저 종전 동호수 삭제
                    old_houseunit.save()

                    # 3. 동호수 연결
                    if houseunit_pk:
                        house_unit.key_unit = instance.keyunit  # 변경 동호수를 기존 계약유닛과 연결
                        house_unit.save()
            except ObjectDoesNotExist:  # 종전 동호수가 없는 경우
                # 3. 동호수 연결
                if houseunit_pk:
                    house_unit.key_unit = keyunit  # 동호수를 계약유닛과 연결
                    house_unit.save()

        # 4. 계약가격 정보 등록
        price = get_cont_price(instance, house_unit)
        pay_amount = get_pay_amount(instance, price[0])

        try:  # 계약가격 정보 존재 여부 확인
            cont_price = instance.contractprice
        except ContractPrice.DoesNotExist:
            cont_price = None

        if cont_price:  # 계약가격 데이터가 존재하는 경우
            if not same_unit_exist:  # 동호수가 생성 또는 변경 된 경우
                # 계약 가격 정보 업데이트
                cont_price.price = price[0]
                cont_price.price_build = price[1]
                cont_price.price_land = price[2]
                cont_price.price_tax = price[3]
                cont_price.down_pay = pay_amount[0]
                cont_price.middle_pay = pay_amount[1]
                cont_price.remain_pay = pay_amount[2]
                cont_price.save()

        else:  # 계약가격 데이터가 존재하지 않는 경우 계약 가격 정보 생성
            cont_price = ContractPrice(contract=instance,
                                       price=price[0],
                                       price_build=price[1],
                                       price_land=price[2],
                                       price_tax=price[3],
                                       down_pay=pay_amount[0],
                                       middle_pay=pay_amount[1],
                                       remain_pay=pay_amount[2])
            cont_price.save()

        # 5. 계약자 정보 테이블 입력
        contractor_name = self.initial_data.get('name')
        birth_date = self.initial_data.get('birth_date', None)
        contractor_gender = self.initial_data.get('gender')
        qualification = self.initial_data.get('qualification', None)
        contractor_status = self.initial_data.get('status')
        reservation_date = self.initial_data.get('reservation_date', None)
        contract_date = self.initial_data.get('contract_date', None)
        contractor_note = self.initial_data.get('note')

        contractor = Contractor.objects.get(contract=instance)
        contractor.name = contractor_name
        contractor.birth_date = birth_date if birth_date else contractor.birth_date
        contractor.gender = contractor_gender
        contractor.qualification = qualification if qualification else '1'
        contractor.status = contractor_status
        contractor.reservation_date = reservation_date if reservation_date else contractor.reservation_date
        contractor.contract_date = contract_date if contract_date else contractor.contract_date
        contractor.note = contractor_note
        contractor.save()

        # 6. 계약자 주소 테이블 입력
        address_id_zipcode = self.initial_data.get('id_zipcode')
        address_id_address1 = self.initial_data.get('id_address1')
        address_id_address2 = self.initial_data.get('id_address2')
        address_id_address3 = self.initial_data.get('id_address3')
        address_dm_zipcode = self.initial_data.get('dm_zipcode')
        address_dm_address1 = self.initial_data.get('dm_address1')
        address_dm_address2 = self.initial_data.get('dm_address2')
        address_dm_address3 = self.initial_data.get('dm_address3')

        contractor_address = ContractorAddress.objects.get(contractor=contractor)
        contractor_address.id_zipcode = address_id_zipcode
        contractor_address.id_address1 = address_id_address1
        contractor_address.id_address2 = address_id_address2
        contractor_address.id_address3 = address_id_address3
        contractor_address.dm_zipcode = address_dm_zipcode
        contractor_address.dm_address1 = address_dm_address1
        contractor_address.dm_address2 = address_dm_address2
        contractor_address.dm_address3 = address_dm_address3
        contractor_address.save()

        # 7. 계약자 연락처 테이블 입력
        contact_cell_phone = self.initial_data.get('cell_phone')
        contact_home_phone = self.initial_data.get('home_phone')
        contact_other_phone = self.initial_data.get('other_phone')
        contact_email = self.initial_data.get('email')

        contractor_contact = ContractorContact.objects.get(contractor=contractor)
        contractor_contact.cell_phone = contact_cell_phone
        contractor_contact.home_phone = contact_home_phone
        contractor_contact.other_phone = contact_other_phone
        contractor_contact.email = contact_email
        contractor_contact.save()

        # 8. 계약금 -- 수납 정보 테이블 입력
        if self.initial_data.get('deal_date'):
            payment_id = self.initial_data.get('payment')
            project = self.initial_data.get('project')
            payment_project = Project.objects.get(pk=project)
            order_group_sort = int(self.initial_data.get('order_group_sort'))
            payment_account_d2 = ProjectAccountD2.objects.get(pk=order_group_sort)
            acc_d3 = 1 if order_group_sort == 1 else 4  # 분담금일 경우 1, 분양대금일 경우 4
            payment_account_d3 = ProjectAccountD3.objects.get(pk=acc_d3)
            ins_order = self.initial_data.get('installment_order')
            payment_installment_order = InstallmentPaymentOrder.objects.get(pk=ins_order)
            payment_serial_number = self.initial_data.get('serial_number')
            payment_trader = self.initial_data.get('trader')
            bank_account = self.initial_data.get('bank_account')
            payment_bank_account = ProjectBankAccount.objects.get(pk=bank_account)
            payment_income = self.initial_data.get('income')
            payment_deal_date = self.initial_data.get('deal_date')

            if payment_id:
                update_payment = ProjectCashBook.objects.get(pk=payment_id)
                update_payment.trader = payment_trader
                update_payment.bank_account = payment_bank_account
                update_payment.income = payment_income
                update_payment.deal_date = payment_deal_date
                update_payment.save()
            else:
                create_payment = ProjectCashBook.objects.create(project=payment_project,
                                                                sort=AccountSort.objects.get(pk=1),
                                                                project_account_d2=payment_account_d2,
                                                                project_account_d3=payment_account_d3,
                                                                contract=instance,
                                                                installment_order=payment_installment_order,
                                                                content=f'{contractor_name}[{payment_serial_number}] 대금납부',
                                                                trader=payment_trader,
                                                                bank_account=payment_bank_account,
                                                                income=payment_income,
                                                                deal_date=payment_deal_date)
                create_payment.save()

        return instance


class ContractPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractPrice
        fields = ('pk', 'contract', 'price', 'price_build', 'price_land',
                  'price_tax', 'down_pay', 'middle_pay', 'remain_pay')


class SubsSummarySerializer(serializers.ModelSerializer):
    unit_type = serializers.IntegerField()
    num_cont = serializers.IntegerField()

    class Meta:
        model = Contract
        fields = ('unit_type', 'num_cont')


class ContSummarySerializer(serializers.ModelSerializer):
    order_group = serializers.IntegerField()
    unit_type = serializers.IntegerField()
    conts_num = serializers.IntegerField()
    price_sum = serializers.IntegerField()

    class Meta:
        model = Contract
        fields = ('order_group', 'unit_type', 'conts_num', 'price_sum')


class ContractInContractorSerializer(serializers.ModelSerializer):
    keyunit = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Contract
        fields = ('pk', 'serial_number', 'keyunit')


class SuccessionInContractorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Succession
        fields = ('pk', 'is_approval')


class ContractorSerializer(serializers.ModelSerializer):
    qualifi_display = serializers.CharField(source='get_qualification_display', read_only=True)
    succession = SuccessionInContractorSerializer(source='curr_contractor', read_only=True)
    contractorrelease = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Contractor
        fields = ('pk', 'contract', 'name', '__str__', 'birth_date', 'gender',
                  'qualification', 'qualifi_display', 'status', 'reservation_date',
                  'contract_date', 'is_active', 'note', 'succession', 'contractorrelease')


class ContractorAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorAddress
        fields = ('pk', 'contractor', 'id_zipcode', 'id_address1', 'id_address2', 'id_address3',
                  'dm_zipcode', 'dm_address1', 'dm_address2', 'dm_address3')


class ContractorContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorContact
        fields = ('pk', 'contractor', 'cell_phone', 'home_phone', 'other_phone', 'email')


class ContractInSuccessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ('pk', 'serial_number')


class SellerInSuccessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contractor
        fields = ('pk', 'name')


class BuyerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorAddress
        fields = ('pk', 'id_zipcode', 'id_address1', 'id_address2', 'id_address3',
                  'dm_zipcode', 'dm_address1', 'dm_address2', 'dm_address3')


class BuyerContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorContact
        fields = ('pk', 'cell_phone', 'home_phone', 'other_phone', 'email')


class BuyerInSuccessionSerializer(serializers.ModelSerializer):
    contractoraddress = BuyerAddressSerializer(read_only=True)
    contractorcontact = BuyerContactSerializer(read_only=True)

    class Meta:
        model = Contractor
        fields = ('pk', 'name', 'birth_date', 'gender', 'contractoraddress', 'contractorcontact')


class SuccessionSerializer(serializers.ModelSerializer):
    contract = ContractInSuccessionSerializer(read_only=True)
    seller = SellerInSuccessionSerializer(read_only=True)
    buyer = BuyerInSuccessionSerializer(read_only=True)

    class Meta:
        model = Succession
        fields = ('pk', 'contract', 'seller', 'buyer', 'apply_date',
                  'trading_date', 'is_approval', 'approval_date', 'note')

    @transaction.atomic
    def create(self, validated_data):
        # 1. contract 데이터 추출
        validated_data['contract_id'] = self.initial_data.get('contract')
        contract = Contract.objects.get(pk=validated_data['contract_id'])

        # 2. 기존 계약자(양도인) 처리 (해지 신청 중인 경우 신청 취소 처리)
        seller = contract.contractor
        seller.contract = None
        seller.prev_contract = contract
        seller.status = '5'
        seller.is_active = False
        seller.save()

        # 해지신청 계약자인지 확인
        try:
            release = seller.contractorrelease
            if release:
                release.status = '0'
                release.save()
        except ObjectDoesNotExist:
            pass

        # 3. 양수계약자 데이터 생성
        qualification = '1' if contract.order_group.sort == '2' else '2'  # 일반분양이면 일반('1') 조합이면 미인가('2')

        buyer = Contractor(contract=contract,
                           name=self.initial_data.get('name'),
                           birth_date=self.initial_data.get('birth_date'),
                           gender=self.initial_data.get('gender'),
                           qualification=qualification,
                           status='2',
                           contract_date=validated_data.get('apply_date'),  # 승계신청일을 계약일자로 기록
                           note=validated_data.get('note'))
        buyer.save()

        # 4. 양수계약자 주소정보 입력
        buyer_addr = ContractorAddress(contractor=buyer,
                                       id_zipcode=self.initial_data.get('id_zipcode'),
                                       id_address1=self.initial_data.get('id_address1'),
                                       id_address2=self.initial_data.get('id_address2'),
                                       id_address3=self.initial_data.get('id_address3'),
                                       dm_zipcode=self.initial_data.get('dm_zipcode'),
                                       dm_address1=self.initial_data.get('dm_address1'),
                                       dm_address2=self.initial_data.get('dm_address2'),
                                       dm_address3=self.initial_data.get('dm_address3'))
        buyer_addr.save()

        # 5. 양수계약자 연락처정보 입력
        buyer_contact = ContractorContact(contractor=buyer,
                                          cell_phone=self.initial_data.get('cell_phone'),
                                          home_phone=self.initial_data.get('home_phone'),
                                          other_phone=self.initial_data.get('other_phone'),
                                          email=self.initial_data.get('email'))
        buyer_contact.save()

        # 6. 권리 의무 승계 정보 입력
        validated_data['seller_id'] = self.initial_data.get('seller')
        validated_data['buyer'] = buyer
        succession = Succession.objects.create(**validated_data)
        succession.save()

        return succession

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.__dict__.update(**validated_data)
        instance.save()

        # 2. 양수계약자 데이터 저장
        buyer = instance.buyer  # 양수계약자 정보
        buyer.name = self.initial_data.get('name')
        buyer.birth_date = self.initial_data.get('birth_date')
        buyer.gender = self.initial_data.get('gender')
        buyer.contract_date = validated_data.get('apply_date')  # 승계신청일을 계약일자로 기록
        buyer.note = f"{buyer.note + '\n' if buyer.note else ''}{validated_data.get('note')}"
        buyer.save()

        buyer_addr = buyer.contractoraddress
        buyer_addr.id_zipcode = self.initial_data.get('id_zipcode')
        buyer_addr.id_address1 = self.initial_data.get('id_address1')
        buyer_addr.id_address2 = self.initial_data.get('id_address2')
        buyer_addr.id_address3 = self.initial_data.get('id_address3')
        buyer_addr.dm_zipcode = self.initial_data.get('dm_zipcode')
        buyer_addr.dm_address1 = self.initial_data.get('dm_address1')
        buyer_addr.dm_address2 = self.initial_data.get('dm_address2')
        buyer_addr.dm_address3 = self.initial_data.get('dm_address3')
        buyer_addr.save()

        buyer_contact = buyer.contractorcontact
        buyer_contact.cell_phone = self.initial_data.get('cell_phone')
        buyer_contact.home_phone = self.initial_data.get('home_phone')
        buyer_contact.other_phone = self.initial_data.get('other_phone')
        buyer_contact.email = self.initial_data.get('email')
        buyer_contact.save()

        # 3. 변경인가완료 처리 여부 확인

        contract = instance.contract
        qua_true = '1' if contract.order_group.sort == '2' else '3'  # 일반분양이면 일반('1') 조합이면 인가('3')
        qua_false = '1' if contract.order_group.sort == '2' else '2'  # 일반분양이면 일반('1') 조합이면 미인가('2')

        # 최초 변경인가 처리 변경 시 (조합원이면 인가/미인가 상태 적용)
        seller = instance.seller
        if instance.is_approval is True:  # 변경인가 완료로 변경 시
            buyer.qualification = qua_true
            seller.qualification = qua_false
        else:  # 변경인가 진행중으로 변경 시
            buyer.qualification = qua_false
            seller.qualification = qua_true
        buyer.save()
        seller.save()

        return instance


class ContractorReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorRelease
        fields = ('pk', 'project', 'contractor', '__str__', 'status', 'refund_amount',
                  'refund_account_bank', 'refund_account_number', 'refund_account_depositor',
                  'request_date', 'completion_date', 'note')

    @transaction.atomic
    def update(self, instance, validated_data):
        contractor = instance.contractor  # 계약자 오브젝트
        released_done = True if instance.status in ('4', '5') else False  # 해지완결 여부

        # 미완료인 상태에서 4 -> 처리완료, 5 -> 자격상실 :: 최초의 최종 해지 확정 처리 1회 실행
        if not released_done and validated_data.get('status') in ('4', '5'):
            # 1. 계약 상태 변경
            completion_date = self.initial_data.get('completion_date')
            contract = contractor.contract
            contract.serial_number = f"{contract.serial_number}-terminated-{completion_date}"
            contract.activation = False  # 일련번호 활성 해제
            contract.save()

            # 2. 키유닛과 계약 간 연결 해제
            keyunit = KeyUnit.objects.get(contract=contract)
            keyunit.contract = None
            keyunit.save()

            # 3. 동호수 연결 해제
            unit = None
            try:  # 동호수 존재 여부 확인
                unit = keyunit.houseunit
            except ObjectDoesNotExist:
                pass
            if unit:  # 동호수 존재 시 삭제
                unit.key_unit = None
                unit.save()

            # 4. 해당 납부분담금 환불처리
            sort = AccountSort.objects.get(pk=1)  # 입금 종류 선택(1=입금, 2=출금)
            payments = ProjectCashBook.objects.filter(sort=sort, contract=contract)  # 해당 계약 입금건 전체
            for payment in payments:
                if not released_done:  # 해지 확정 전일 때만 실행
                    refund_d3 = int(payment.project_account_d3.id) + 1  # 분양대금 or 분담금 환불처리 건으로 계정
                    payment.project_account_d3 = ProjectAccountD3.objects.get(pk=refund_d3)  # 환불처리 계정으로 변경
                    payment.refund_contractor = contractor  # 환불 계약자 등록
                if completion_date:  # 최종 해지(환불)처리일 정보가 있으면
                    msg = f'환불 계약 건 - {payment.contract.serial_number[:13]} ({completion_date} {contractor.name} 환불완료)'
                    append_note = ', ' + msg if payment.note else msg
                    payment.note = payment.note + append_note  # 비고란 최종 메시지 입력
                payment.save()

            # 5.  계약자 정보 최종 해지상태로 변경
            contractor.prev_contract = contract
            contractor.contract = None
            if contractor.qualification == '3':
                contractor.qualification = '2'  # 인가 등록 취소
            contractor.is_active = False  # 비활성 상태로 변경
            contractor.status = '4'  # 해지 상태로 변경
            contractor.save()

        # 1. 해지정보 테이블 입력
        instance.__dict__.update(**validated_data)
        instance.save()

        return instance
