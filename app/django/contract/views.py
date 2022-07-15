from django import forms
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q, Max
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import ListView, FormView, TemplateView

from .models import (OrderGroup, Contract, Contractor,
                     ContractorAddress, ContractorContact, ContractorRelease)
from rebs.models import ProjectAccountSort, ProjectAccountD1, ProjectAccountD2
from project.models import Project, UnitType, KeyUnit, BuildingUnit, HouseUnit
from cash.models import ProjectBankAccount, ProjectCashBook, InstallmentPaymentOrder

from .forms import ContractRegisterForm, ContractPaymentForm, ContractorReleaseForm


class ContractLV(LoginRequiredMixin, ListView):
    model = Contract

    def get_paginate_by(self, queryset):
        return self.request.GET.get('limit') if self.request.GET.get('limit') else 15

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_queryset(self):
        project = self.get_project()
        contract = Contract.objects.filter(project=project,
                                           contractor__status='2').order_by('-created_at')
        if self.request.GET.get('group'):
            contract = contract.filter(order_group=self.request.GET.get('group'))
        if self.request.GET.get('type'):
            contract = contract.filter(unit_type=self.request.GET.get('type'))
        if self.request.GET.get('dong'):
            contract = contract.filter(keyunit__houseunit__building_unit=self.request.GET.get('dong'))
        if self.request.GET.get('status'):
            contract = contract.filter(contractor__contractorrelease__status=self.request.GET.get('status'))
        if self.request.GET.get('register'):
            result = True if self.request.GET.get('register') == '1' else False
            contract = contract.filter(contractor__is_registed=result)
        order_list = ['-created_at', 'created_at', '-contractor__contract_date',
                      'contractor__contract_date', '-serial_number',
                      'serial_number', '-contractor__name', 'contractor__name']
        if self.request.GET.get('order'):
            contract = contract.order_by(order_list[int(self.request.GET.get('order'))])
        if self.request.GET.get('sdate'):
            contract = contract.filter(contractor__contract_date__gte=self.request.GET.get('sdate'))
        if self.request.GET.get('edate'):
            contract = contract.filter(contractor__contract_date__lte=self.request.GET.get('edate'))
        if self.request.GET.get('q'):
            q = self.request.GET.get('q')
            contract = contract.filter(Q(serial_number__icontains=q) |
                                       Q(contractor__name__icontains=q) |
                                       Q(contractor__note__icontains=q))
        return contract

    def get_context_data(self, **kwargs):
        context = super(ContractLV, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['groups'] = OrderGroup.objects.filter(project=self.get_project())
        context['types'] = UnitType.objects.filter(project=self.get_project())
        context['dongs'] = BuildingUnit.objects.filter(project=self.get_project())

        ### 계약 요약 테이블 데이터
        unit_num = []  # 타입별 세대수
        reserv_num = []  # 타입별 청약건
        contract_num = []  # 차수별 타입별 계약건

        context['total_unit_num'] = 0
        context['total_reserv_num'] = 0
        tcn = []
        ocn = []

        for i, type in enumerate(context['types']):
            units = HouseUnit.objects.filter(unit_type=type).count()  # 타입별 세대수
            reservs = Contractor.objects.filter(contract__project=self.get_project(),
                                                contract__unit_type=type,
                                                status='1').count()
            unit_num.append(units)  # 타입별 세대수
            reserv_num.append(reservs)  # 타입별 청약건
            context['total_unit_num'] += unit_num[i]  # 타입별 세대수 합계
            context['total_reserv_num'] += reserv_num[i]  # 타입별 청약건 합계
            cnum = []  # 차수별 타입별 계약건수
            ocn = []  # ??
            for j, og in enumerate(context['groups']):  # 차수
                cnum.append(Contract.objects.filter(project=self.get_project(),
                                                    unit_type=type,
                                                    activation=True,
                                                    contractor__status='2',
                                                    order_group=og).count())
                ocn.append(Contract.objects.filter(project=self.get_project(),
                                                   activation=True,
                                                   contractor__status='2',
                                                   order_group=og).count())

            contract_num.append(list(reversed(cnum)))
            tcn.append(sum(cnum))

        context['unit_num'] = list(reversed(unit_num))
        context['reserv_num'] = list(reversed(reserv_num))
        context['contract_num'] = list(reversed(contract_num))
        context['tcn'] = list(reversed(tcn))
        context['ocn'] = list(reversed(ocn))
        context['total_tcn'] = sum(tcn)

        context['reservation_list'] = Contract.objects.filter(project=self.get_project(),
                                                              contractor__status=1)
        context['contract_count'] = self.get_queryset().count()
        return context


class ContractRegisterView(LoginRequiredMixin, FormView):
    form_class = ContractRegisterForm
    template_name = 'contract/contract_form.html'
    PaymentInlineFormSet = forms.models.inlineformset_factory(
        Contract,
        ProjectCashBook,
        form=ContractPaymentForm,
        extra=0
    )

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_back_url(self):
        page = self.request.GET.get('p')
        limit = self.request.GET.get('l')
        group = self.request.GET.get('g')
        type = self.request.GET.get('t')
        dong = self.request.GET.get('d')
        status = self.request.GET.get('s')
        register = self.request.GET.get('r')
        order = self.request.GET.get('o')
        sdate = self.request.GET.get('sd')
        edate = self.request.GET.get('ed')
        q = self.request.GET.get('q')

        pjid = str(self.get_project().id) if self.get_project() else ''
        project_str = 'project=' + pjid
        query_str = '?page=' + page + '&' + project_str if page else '?' + project_str
        query_str = query_str + '&limit=' + limit if limit else query_str
        query_str = query_str + '&group=' + group if group else query_str
        query_str = query_str + '&type=' + type if type else query_str
        query_str = query_str + '&dong=' + dong if dong else query_str
        query_str = query_str + '&status=' + status if status else query_str
        query_str = query_str + '&register=' + register if register else query_str
        query_str = query_str + '&order=' + order if order else query_str
        query_str = query_str + '&sdate=' + sdate if sdate else query_str
        query_str = query_str + '&edate=' + edate if edate else query_str
        query_str = query_str + '&q=' + q if q else query_str
        return reverse_lazy('rebs:contract:index') + query_str

    def get_form(self, form_class=None):
        initial = {
            'project': self.get_project().pk if self.get_project() else None,
            'task': self.request.GET.get('task'),
            'order_group': self.request.GET.get('order_group'),
            'type': self.request.GET.get('type'),
            'key_unit': self.request.GET.get('key_unit'),
            'house_unit': self.request.GET.get('house_unit'),
            'back_url': self.get_back_url(),
        }
        if self.request.GET.get('cont_id'):
            contractor = Contractor.objects.get(contract=Contract.objects.get(pk=self.request.GET.get('cont_id')))
            contact = ContractorContact.objects.get(contractor=contractor)
            address = ContractorAddress.objects.get(contractor=contractor)
            initial['name'] = contractor.name
            initial['birth_date'] = contractor.birth_date
            initial['gender'] = contractor.gender
            initial['is_registed'] = contractor.is_registed
            initial['reservation_date'] = contractor.reservation_date
            initial['contract_date'] = contractor.contract_date
            initial['note'] = contractor.note
            initial['cell_phone'] = contact.cell_phone
            initial['home_phone'] = contact.home_phone
            initial['other_phone'] = contact.other_phone
            initial['email'] = contact.email
            initial['id_zipcode'] = address.id_zipcode
            initial['id_address1'] = address.id_address1
            initial['id_address2'] = address.id_address2
            initial['id_address3'] = address.id_address3
            initial['dm_zipcode'] = address.dm_zipcode
            initial['dm_address1'] = address.dm_address1
            initial['dm_address2'] = address.dm_address2
            initial['dm_address3'] = address.dm_address3
        return self.form_class(initial=initial)

    def get_context_data(self, **kwargs):
        context = super(ContractRegisterView, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['order_groups'] = OrderGroup.objects.filter(project=self.get_project())
        context['types'] = UnitType.objects.filter(project=self.get_project())
        key_units = KeyUnit.objects.filter(project=self.get_project(),
                                           unit_type=self.request.GET.get('type'),
                                           contract__isnull=True)
        cont_id = self.request.GET.get('cont_id')
        if cont_id:
            key_units = KeyUnit.objects.filter(Q(pk=self.request.GET.get('key_unit')) |
                                               Q(project=self.get_project(),
                                                 unit_type=self.request.GET.get('type'),
                                                 contract__isnull=True))
        context['key_units'] = key_units if cont_id else key_units[:10]
        context['house_units'] = HouseUnit.objects.filter(project=self.get_project(),
                                                          unit_type=self.request.GET.get('type'),
                                                          key_unit__isnull=True)
        if self.request.GET.get('house_unit'):
            context['house_units'] = HouseUnit.objects.filter(Q(pk=self.request.GET.get('house_unit')) |
                                                              Q(project=self.get_project(),
                                                                unit_type=self.request.GET.get('type'),
                                                                key_unit__isnull=True))
        context['project_bank_accounts'] = ProjectBankAccount.objects.filter(project=self.get_project())
        pay_code = '4' if cont_id else '2'
        context['installment_orders'] = InstallmentPaymentOrder.objects.filter(project=self.get_project(),
                                                                               pay_code__lte=pay_code)
        context['formset'] = self.PaymentInlineFormSet(queryset=ProjectCashBook.objects.none(),
                                                       form_kwargs={'project': self.get_project()})
        if cont_id:
            contract = context['contract'] = Contract.objects.get(pk=cont_id)
            contractor = context['contractor'] = contract.contractor
            context['task'] = contractor.status if contractor.status >= '3' else '3'
            context['formset'] = self.PaymentInlineFormSet(instance=contract,
                                                           queryset=ProjectCashBook.objects.filter(contract=contract,
                                                                                                   installment_order__pay_sort='1').order_by(
                                                               'deal_date'),
                                                           form_kwargs={'project': self.get_project()})
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        cont_id = self.request.GET.get('cont_id')

        if form.is_valid():

            with transaction.atomic():  # 트랜잭션

                # 1. 계약정보 테이블 입력
                if not cont_id:
                    contract = Contract(project=Project.objects.get(pk=self.request.POST.get('project')),
                                        order_group=OrderGroup.objects.get(pk=self.request.POST.get('order_group')),
                                        unit_type=UnitType.objects.get(pk=self.request.POST.get('type')),
                                        serial_number=f"{KeyUnit.objects.get(pk=self.request.POST.get('key_unit')).unit_code}-{self.request.POST.get('order_group')}",
                                        user=self.request.user)
                else:
                    contract = Contract.objects.get(pk=cont_id)
                    contract.order_group = OrderGroup.objects.get(pk=self.request.POST.get('order_group'))
                    contract.unit_type = UnitType.objects.get(pk=self.request.POST.get('type'))
                    contract.serial_number = f"{KeyUnit.objects.get(pk=self.request.POST.get('key_unit')).unit_code}-{self.request.POST.get('order_group')}"
                    contract.user = self.request.user
                contract.save()

                # 2. 계약 유닛 연결
                if not cont_id:
                    keyunit = KeyUnit.objects.get(pk=self.request.POST.get('key_unit'))
                    keyunit.contract = contract
                    keyunit.save()
                else:
                    # 1) 종전 동호수 연결 해제
                    try:
                        pastUN = contract.keyunit.houseunit
                        pastUN.key_unit = None  # 종전 계약의 동호수 삭제
                        pastUN.save()
                    except ObjectDoesNotExist:
                        pass

                    # 3. 계약 유닛 연결
                    pastCU = contract.keyunit
                    pastCU.contract = None  # 종전 계약의 계약유닛 삭제
                    pastCU.save()
                    keyunit = KeyUnit.objects.get(pk=self.request.POST.get('key_unit'))
                    keyunit.contract = contract
                    keyunit.save()

                # 3. 동호수 연결
                if self.request.POST.get('house_unit'):
                    house_unit = HouseUnit.objects.get(pk=self.request.POST.get('house_unit'))
                    house_unit.key_unit = keyunit
                    house_unit.save()

                # 4. 계약자 정보 테이블 입력
                if not cont_id:
                    contractor = Contractor(contract=contract,
                                            name=form.cleaned_data.get('name'),
                                            birth_date=form.cleaned_data.get('birth_date'),
                                            gender=form.cleaned_data.get('gender'),
                                            is_registed=form.cleaned_data.get('is_registed'),
                                            status=self.request.POST.get('task'),
                                            reservation_date=form.cleaned_data.get('reservation_date'),
                                            contract_date=form.cleaned_data.get('contract_date'),
                                            note=form.cleaned_data.get('note'),
                                            user=self.request.user)
                else:
                    contractor = Contractor.objects.get(contract=contract)
                    contractor.name = form.cleaned_data.get('name')
                    contractor.birth_date = form.cleaned_data.get('birth_date')
                    contractor.gender = form.cleaned_data.get('gender')
                    contractor.is_registed = form.cleaned_data.get('is_registed')
                    contractor.status = form.cleaned_data.get('task')
                    contractor.reservation_date = form.cleaned_data.get('reservation_date')
                    contractor.contract_date = form.cleaned_data.get('contract_date')
                    contractor.note = form.cleaned_data.get('note')
                    contractor.user = self.request.user
                contractor.save()

                # 5. 계약자 주소 테이블 입력
                if not cont_id:
                    contractorAddress = ContractorAddress(contractor=contractor,
                                                          id_zipcode=form.cleaned_data.get('id_zipcode'),
                                                          id_address1=form.cleaned_data.get('id_address1'),
                                                          id_address2=form.cleaned_data.get('id_address2'),
                                                          id_address3=form.cleaned_data.get('id_address3'),
                                                          dm_zipcode=form.cleaned_data.get('dm_zipcode'),
                                                          dm_address1=form.cleaned_data.get('dm_address1'),
                                                          dm_address2=form.cleaned_data.get('dm_address2'),
                                                          dm_address3=form.cleaned_data.get('dm_address3'),
                                                          user=self.request.user)
                else:
                    contractorAddress = ContractorAddress.objects.get(contractor=contractor)
                    contractorAddress.id_zipcode = form.cleaned_data.get('id_zipcode')
                    contractorAddress.id_address1 = form.cleaned_data.get('id_address1')
                    contractorAddress.id_address2 = form.cleaned_data.get('id_address2')
                    contractorAddress.id_address3 = form.cleaned_data.get('id_address3')
                    contractorAddress.dm_zipcode = form.cleaned_data.get('dm_zipcode')
                    contractorAddress.dm_address1 = form.cleaned_data.get('dm_address1')
                    contractorAddress.dm_address2 = form.cleaned_data.get('dm_address2')
                    contractorAddress.dm_address3 = form.cleaned_data.get('dm_address3')
                    contractorAddress.user = self.request.user
                contractorAddress.save()

                # 6. 계약자 연락처 테이블 입력
                if not cont_id:
                    contractorContact = ContractorContact(contractor=contractor,
                                                          cell_phone=form.cleaned_data.get('cell_phone'),
                                                          home_phone=form.cleaned_data.get('home_phone'),
                                                          other_phone=form.cleaned_data.get('other_phone'),
                                                          email=form.cleaned_data.get('email'),
                                                          user=self.request.user)
                else:
                    contractorContact = ContractorContact.objects.get(contractor=contractor)
                    contractorContact.cell_phone = form.cleaned_data.get('cell_phone')
                    contractorContact.home_phone = form.cleaned_data.get('home_phone')
                    contractorContact.other_phone = form.cleaned_data.get('other_phone')
                    contractorContact.email = form.cleaned_data.get('email')
                    contractorContact.user = self.request.user
                contractorContact.save()

                # 7. 계약금 -- 수납 정보 테이블 입력 -- PaymentInlineFormSet 처리
                if not cont_id:
                    formset = self.PaymentInlineFormSet(self.request.POST,
                                                        form_kwargs={'project': self.request.POST.get('project')})
                else:
                    formset = self.PaymentInlineFormSet(self.request.POST,
                                                        form_kwargs={'project': self.request.POST.get('project')},
                                                        instance=contract)

                if formset.is_valid():
                    cont_note = form.cleaned_data.get('note')
                    for form in formset:
                        pCashbook = form.save(commit=False)
                        pCashbook.project = Project.objects.get(pk=self.request.POST.get('project'))
                        pCashbook.sort = ProjectAccountSort.objects.get(pk=1)
                        dSort = int(contract.order_group.sort)
                        pCashbook.project_account_d1 = ProjectAccountD1.objects.get(pk=dSort)
                        pCashbook.project_account_d2 = ProjectAccountD2.objects.get(pk=dSort)
                        pCashbook.is_contract_payment = True
                        if not cont_id:
                            pCashbook.contract = contract
                        pCashbook.note = cont_note
                        pCashbook.user = self.request.user
                        pCashbook.save()

                return redirect(self.get_back_url())
        else:
            return render(request, 'contract/contract_form.html', {'formset': formset})


class ContractorUpdate(LoginRequiredMixin, FormView):
    pass


class ContractorTrans(LoginRequiredMixin, FormView):
    model = Contractor

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_context_data(self, **kwargs):
        context = super(ContractorTrans, self).get_context_data(**kwargs)
        context['project_list'] = self.request.user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        return context


class ContractorReleaseRegister(LoginRequiredMixin, ListView, FormView):
    model = ContractorRelease
    form_class = ContractorReleaseForm
    paginate_by = 10
    template_name = 'contract/release_form.html'

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_form(self, form_class=None):
        initial = {
            'project': self.get_project(),
            'contractor': self.request.GET.get('contractor'),
            'status': self.request.GET.get('task'),
            'user': self.request.user
        }
        release_id = self.request.GET.get('release_id')
        if release_id:
            release = ContractorRelease.objects.get(pk=release_id)
            initial['refund_amount'] = release.refund_amount
            initial['refund_account_bank'] = release.refund_account_bank
            initial['refund_account_number'] = release.refund_account_number
            initial['refund_account_depositor'] = release.refund_account_depositor
            initial['request_date'] = release.request_date
            initial['completion_date'] = release.completion_date
            initial['note'] = release.note
        return self.form_class(initial=initial)

    def get_context_data(self, **kwargs):
        context = super(ContractorReleaseRegister, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['contractors'] = Contractor.objects.filter(contract__project=self.get_project(), status='2')
        if self.request.GET.get('contractor'):
            context['contractors'] = Contractor.objects.filter(pk=self.request.GET.get('contractor'))
            context['contractor'] = Contractor.objects.get(pk=self.request.GET.get('contractor'))
            context['contract'] = context['contractor'].contract
        context['total_release'] = self.model.objects.filter(project=self.get_project()).count()
        return context

    def get_queryset(self):
        release = self.model.objects.filter(project=self.get_project(), status__gte='3').order_by('-id')
        return release

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if request.GET.get('release_id'):
            release = ContractorRelease.objects.get(pk=request.GET.get('release_id'))
            form = self.form_class(request.POST, instance=release)

        if form.is_valid():
            with transaction.atomic():  # 트랜잭션

                if request.GET.get('task') >= '4':

                    # 1. 계약자 정보 현재 상태 변경
                    contractor = Contractor.objects.get(pk=request.POST.get('contractor'))
                    contract = Contract.objects.get(pk=contractor.contract.id)
                    keyunit = KeyUnit.objects.get(contract__contractor=contractor)

                    try:
                        released_done = contractor.contractorrelease.status >= '4'
                    except:
                        released_done = False

                    if not released_done:
                        contractor.is_registed = False  # 인가 등록 여부
                        contractor.status = str(int(contractor.status) + 2)  # 해지 상태로 변경
                    contractor.user = request.user  # 해지 등록 작업자
                    contractor.save()
                    # 2. 계약 상태 변경
                    if not released_done:
                        contract.serial_number = str(contract.serial_number) + '-terminated-' + str(
                            form.cleaned_data.get('completion_date'))
                        contract.activation = False  # 일련번호 활성 해제
                        contract.save()
                    # 3. 계약유닛 연결 해제
                    contract.keyunit.houseunit
                    if not released_done:
                        keyunit.contract = None
                        keyunit.save()
                    # 4. 동호수 연결 해제
                    if not released_done:
                        try:  # 동호수 존재 여부 확인
                            unit = keyunit.houseunit
                        except Exception:
                            unit = None
                        if unit:
                            unit.key_unit = None
                            unit.save()
                    # 5. 해당 납부분담금 환불처리
                    projectCash = ProjectCashBook.objects.filter(sort='1', contract=contractor.contract)
                    for pc in projectCash:
                        if not released_done:
                            refund_d2 = pc.project_account_d1.id + 63
                            pc.project_account_d2 = ProjectAccountD2.objects.get(pk=refund_d2)
                            pc.refund_contractor = contractor
                        if form.cleaned_data.get('completion_date'):
                            msg = str(form.cleaned_data.get('completion_date')) + ' 환불건'
                            append_note = ', ' + msg if pc.note else msg
                            pc.note = pc.note + append_note
                        pc.save()

                # 4. 계약 해지 정보 테이블 입력
                form.save()

                return redirect(reverse_lazy('rebs:contract:release') + '?project=' + str(self.get_project().id))
        else:
            return render(request, 'contract/release_form.html', {'form': form})


class BuildDashboard(LoginRequiredMixin, TemplateView):
    template_name = 'contract/dashboard.html'

    def get_project(self):
        try:
            project = self.request.user.staffauth.assigned_project
        except:
            project = Project.objects.first()
        gp = self.request.GET.get('project')
        project = Project.objects.get(pk=gp) if gp else project
        return project

    def get_context_data(self, **kwargs):
        context = super(BuildDashboard, self).get_context_data(**kwargs)
        user = self.request.user
        context['project_list'] = Project.objects.all() if user.is_superuser else user.staffauth.allowed_projects.all()
        context['this_project'] = self.get_project()
        context['types'] = UnitType.objects.filter(project=self.get_project())
        context['max_floor'] = HouseUnit.objects.aggregate(Max('floor_no'))
        floor_no__max = context['max_floor']['floor_no__max'] if context['max_floor']['floor_no__max'] else 1
        context['max_floor_range'] = range(1, floor_no__max + 1)
        context['house_units'] = HouseUnit.objects.filter(project=self.get_project())
        context['is_hold'] = HouseUnit.objects.filter(project=self.get_project(), is_hold=True)
        context['is_apply'] = Contractor.objects.filter(contract__project=self.get_project(), status='1')
        context['is_contract'] = Contractor.objects.filter(contract__project=self.get_project(), status='2')
        context['dong_list'] = []
        context['line'] = []
        context['units'] = []

        dong_list = list(BuildingUnit.objects.filter(project=self.get_project()).values('name'))

        for dong in dong_list:
            context['dong_list'].append(dong['name'])
            lines = HouseUnit.objects.order_by('-bldg_line').values('bldg_line').filter(
                building_unit__name__contains=dong['name']).distinct()
            ln = []
            for line in lines:
                ln.append(line['bldg_line'])
            context['line'].append(ln)
            context['units'].append(
                HouseUnit.objects.filter(building_unit__name__contains=dong['name']).order_by('-floor_no',
                                                                                              'bldg_line'))

        context['line'] = list(reversed(context['line']))
        context['units'] = list(reversed(context['units']))
        return context
