import api from '@/api'
import {
  FETCH_CONTRACT,
  FETCH_CONTRACTOR,
  FETCH_CONTRACT_LIST,
  FETCH_ORDER_GROUP_LIST,
  FETCH_SUBS_SUMMARY_LIST,
  FETCH_CONT_SUMMARY_LIST,
  FETCH_KEY_UNIT_LIST,
  FETCH_HOUSE_UNIT_LIST,
  FETCH_SALES_PRICE_LIST,
  FETCH_DOWN_PAYMENT_LIST,
  FETCH_CONT_RELEASE_LIST,
  FETCH_CONTRACTOR_LIST,
  FETCH_CONT_RELEASE,
} from '@/store/modules/contract/mutations-types'
import router from '@/router'
import { errorHandle, message } from '@/utils/helper'

const actions = {
  fetchContractList: ({ commit }: any, payload?: any) => {
    const { project } = payload
    const status = payload.status ? payload.status : '2'
    let url = `/contract-set/?project=${project}&activation=true&contractor__status=${status}`
    if (payload.order_group) url += `&order_group=${payload.order_group}`
    if (payload.unit_type) url += `&unit_type=${payload.unit_type}`
    if (payload.building)
      url += `&keyunit__houseunit__building_unit=${payload.building}`
    if (payload.registed) url += `&contractor__is_registed=${payload.registed}`
    if (payload.from_date) url += `&from_contract_date=${payload.from_date}`
    if (payload.to_date) url += `&to_contract_date=${payload.to_date}`
    if (payload.search) url += `&search=${payload.search}`
    const ordering = payload.ordering ? payload.ordering : '-created_at'
    const page = payload.page ? payload.page : 1
    url += `&ordering=${ordering}&page=${page}`
    api
      .get(url)
      .then(res => {
        commit(FETCH_CONTRACT_LIST, res.data)
      })
      .catch(err => errorHandle(err.response.data))
  },

  fetchContract: ({ commit }: any, pk: number) => {
    return api
      .get(`/contract-set/${pk}/`)
      .then(res => {
        commit(FETCH_CONTRACT, res.data)
      })
      .catch(err => errorHandle(err.response.data))
  },

  createContract: async ({ dispatch }: any, payload: any) => {
    // 1. 계약 생성
    try {
      return await api.post(`/contract/`, payload)
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  },

  updateContract: async ({ dispatch }: any, payload: any) => {
    const { pk, ...formData } = payload
    try {
      return await api.put(`/contract/${pk}/`, formData)
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  },

  patchKeyUnit: async ({ dispatch }: any, payload: any) => {
    // 2. keyunit
    const { pk, ...data } = payload
    try {
      await api.patch(`key-unit/${pk}/`, data)
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  },

  patchHouseUnit: async ({ dispatch }: any, payload: any) => {
    // 3. houseunit
    const { pk, ...data } = payload
    try {
      await api.patch(`/house-unit/${pk}/`, data)
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  },

  fetchContractorList: ({ commit }: any, payload: any) => {
    const { project, search } = payload
    return api
      .get(`/contractor/?project=${project}&search=${search}`)
      .then(res => {
        commit(FETCH_CONTRACTOR_LIST, res.data)
      })
      .catch(err => errorHandle(err.response.data))
  },

  fetchContractor: ({ commit }: any, pk: number) => {
    return api
      .get(`/contractor/${pk}/`)
      .then(res => {
        commit(FETCH_CONTRACTOR, res.data)
      })
      .catch(err => errorHandle(err.response.data))
  },

  createContractor: async ({ dispatch }: any, payload: any) => {
    // 4. contractor
    try {
      return await api.post(`/contractor/`, payload)
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  },

  updateContractor: async ({ dispatch }: any, payload: any) => {
    // 4. contractor
    const { pk, ...data } = payload
    try {
      return await api.put(`/contractor/${pk}/`, data)
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  },

  createAddress: async ({ dispatch }: any, payload: any) => {
    // 5. address
    try {
      await api.post(`/contractor-address/`, payload)
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  },

  updateAddress: async ({ dispatch }: any, payload: any) => {
    // 5. address
    const { pk, ...data } = payload
    try {
      await api.put(`/contractor-address/${pk}/`, data)
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  },

  createContact: async ({ dispatch }: any, payload: any) => {
    // 6. contact
    try {
      await api.post(`/contractor-contact/`, payload)
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  },

  updateContact: async ({ dispatch }: any, payload: any) => {
    // 6. contact
    const { pk, ...data } = payload
    try {
      await api.put(`/contractor-contact/${pk}/`, data)
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  },

  createContractSet: async ({ dispatch }: any, payload: any) => {
    // 1. contract 생성
    const { project, order_group, unit_type, key_unit, ...rest1 } = payload
    const ordergroup = order_group.split(',')
    const keyunit = key_unit.split(',')
    const serial_number = `${keyunit[1]}-${ordergroup[0]}`
    const contractPayload = {
      project,
      order_group: ordergroup[0],
      unit_type,
      serial_number,
    }

    const contractObj = await dispatch('createContract', contractPayload)

    // 2. 계약 유닛 연결 ( keyunit -> contract.pk)
    const keyUnitPk = keyunit[0]
    const contPk = contractObj.data.pk
    const keyunitPayload = { pk: keyUnitPk, contract: contPk }

    await dispatch('patchKeyUnit', keyunitPayload)

    // 3. 동호수 연결
    const { houseunit, ...rest3 } = rest1
    const houseUnitPk = houseunit
    const houseUnitData = { pk: houseUnitPk, key_unit: keyUnitPk }

    if (houseunit) await dispatch('patchHouseUnit', houseUnitData)

    // 4. 계약자 정보 테이블 입력
    const {
      name,
      birth_date,
      gender,
      is_registed,
      status,
      reservation_date,
      contract_date,
      note,
      ...rest4
    } = rest3
    const contractorObj = await dispatch('createContractor', {
      contract: contPk,
      name,
      birth_date,
      gender,
      is_registed,
      status,
      reservation_date,
      contract_date,
      note,
    })

    // 5. 계약자 주소 테이블 입력
    const contractor = contractorObj.data.pk
    const {
      id_zipcode,
      id_address1,
      id_address2,
      id_address3,
      dm_zipcode,
      dm_address1,
      dm_address2,
      dm_address3,
      ...rest5
    } = rest4
    if (id_zipcode || dm_zipcode)
      await dispatch('createAddress', {
        contractor,
        id_zipcode,
        id_address1,
        id_address2,
        id_address3,
        dm_zipcode,
        dm_address1,
        dm_address2,
        dm_address3,
      })

    // 6. 계약자 연락처 테이블 입력
    const { cell_phone, home_phone, other_phone, email, ...rest6 } = rest5
    if (cell_phone)
      await dispatch('createContact', {
        contractor,
        cell_phone,
        home_phone,
        other_phone,
        email,
      })

    // 7. 계약금 - 수납 정보 테이블 입력
    const cashData = {
      project,
      sort: 1,
      project_account_d1: ordergroup[1],
      project_account_d2: ordergroup[1],
      is_contract_payment: true,
      contract: contPk,
      content: `${name}[${serial_number} 대금납부]`,
      ...rest6,
    }
    try {
      await api.post(`/project-cashbook/`, cashData)
    } catch (err: any) {
      errorHandle(err.response.data)
    }

    dispatch('fetchContractList', { project, status })
    dispatch(
      'project/fetchHouseUnitList',
      {
        project,
      },
      { root: true },
    )
    message()
  },

  updateContractSet: async ({ dispatch }: any, payload: any) => {
    // 1. contract 업데이트
    const { pk, project, order_group, unit_type, key_unit, ...rest1 } = payload
    const ordergroup = order_group.split(',')
    const keyunit = key_unit.split(',')
    const serial_number = `${keyunit[1]}-${ordergroup[0]}`
    const contractPayload = {
      pk,
      project,
      order_group: ordergroup[0],
      unit_type,
      serial_number,
    }

    const contractObj = await dispatch('updateContract', contractPayload)

    // 2. 계약 유닛 연결 ( keyunit -> contract.pk)
    // --> 1) 종전 동호수 연결 해제
    // -----> 동호수가 연결되어 있는지 확인 -> true 면 실행
    const { cont_keyunit, cont_houseunit, houseunit, ...rest2 } = rest1

    if (keyunit[0] !== cont_keyunit) {
      // 계약 유닛 변경 시
      if (cont_houseunit !== '')
        // 기존에 디비에 저장되어 있는 동호유닛이 있으면
        await dispatch('patchHouseUnit', {
          // 기존 동호 삭제
          pk: cont_houseunit,
          key_unit: null,
        })
      // --> 2) 종전 계약 유닛 삭제
      if (cont_keyunit)
        await dispatch('patchKeyUnit', { pk: cont_keyunit, contract: null })

      // --> 3) 변경 계약 유닛 입력
      const keyUnitPk = keyunit[0]
      const contPk = contractObj.data.pk
      const keyunitPayload = { pk: keyUnitPk, contract: contPk }
      await dispatch('patchKeyUnit', keyunitPayload)
    }

    // 3. 동호수 연결
    if (keyunit[0] !== cont_keyunit || houseunit !== cont_houseunit) {
      // 계약유닛 변경 or 동호유닛 변경 시
      const houseUnitData = { pk: houseunit, key_unit: keyunit[0] }
      if (houseunit) await dispatch('patchHouseUnit', houseUnitData)
    }

    // 4. 계약자 정보 테이블 입력
    const {
      contractorPk,
      name,
      birth_date,
      gender,
      is_registed,
      status,
      reservation_date,
      contract_date,
      note,
      ...rest4
    } = rest2
    const contractorObj = await dispatch('updateContractor', {
      pk: contractorPk,
      contract: contractObj.data.pk,
      name,
      birth_date,
      gender,
      is_registed,
      status,
      reservation_date,
      contract_date,
      note,
    })

    // 5. 계약자 주소 테이블 입력
    const contractor = contractorObj.data.pk
    const {
      addressPk,
      id_zipcode,
      id_address1,
      id_address2,
      id_address3,
      dm_zipcode,
      dm_address1,
      dm_address2,
      dm_address3,
      ...rest5
    } = rest4
    const addressPayload = {
      pk: addressPk,
      contractor,
      id_zipcode,
      id_address1,
      id_address2,
      id_address3,
      dm_zipcode,
      dm_address1,
      dm_address2,
      dm_address3,
    }
    if (id_zipcode || dm_zipcode)
      if (addressPk) await dispatch('updateAddress', addressPayload)
      else await dispatch('createAddress', addressPayload)

    // 6. 계약자 연락처 테이블 입력
    const { contactPk, cell_phone, home_phone, other_phone, email, ...rest6 } =
      rest5
    if (cell_phone)
      await dispatch('updateContact', {
        pk: contactPk,
        contractor,
        cell_phone,
        home_phone,
        other_phone,
        email,
      })

    // 7. 계약금 - 수납 정보 테이블 입력
    const { paymentPk, ...data } = rest6
    const cashData = {
      project,
      sort: 1,
      project_account_d1: ordergroup[1],
      project_account_d2: ordergroup[1],
      is_contract_payment: true,
      contract: contractObj.data.pk,
      content: `${name}[${serial_number} 대금납부]`,
      ...data,
    }
    if (cashData.deal_date) {
      if (!paymentPk) {
        try {
          await api.post(`/project-cashbook/`, cashData)
        } catch (err: any) {
          errorHandle(err.response.data)
        }
      } else {
        try {
          await api.put(`/project-cashbook/${paymentPk}/`, cashData)
        } catch (err: any) {
          errorHandle(err.response.data)
        }
      }
    }

    router.push({
      name: '계약등록 관리',
      query: { contract: contractObj.data.pk },
    })
    dispatch('fetchContract', contractObj.data.pk)
    dispatch('fetchHouseUnitList', {
      project,
      unit_type,
      contract: contractObj.data.pk,
    })
    dispatch(
      'project/fetchHouseUnitList',
      {
        project,
      },
      { root: true },
    )
    message()
  },

  fetchSubsSummaryList: ({ commit }: any, project?: number) => {
    api
      .get(`/subs-sum/?project=${project}`)
      .then(res => {
        commit(FETCH_SUBS_SUMMARY_LIST, res.data)
      })
      .catch(err => errorHandle(err.response.data))
  },

  fetchContSummaryList: ({ commit }: any, project?: number) => {
    api
      .get(`/cont-sum/?project=${project}`)
      .then(res => {
        commit(FETCH_CONT_SUMMARY_LIST, res.data)
      })
      .catch(err => errorHandle(err.response.data))
  },

  fetchOrderGroupList: ({ commit }: any, pk?: number) => {
    api
      .get(`/order-group/?project=${pk}`)
      .then(res => {
        commit(FETCH_ORDER_GROUP_LIST, res.data)
      })
      .catch(err => errorHandle(err.response.data))
  },

  createOrderGroup: ({ dispatch }: any, payload: any) => {
    api
      .post(`/order-group/`, payload)
      .then(res => {
        dispatch('fetchOrderGroupList', res.data.project)
        message()
      })
      .catch(err => errorHandle(err.response.data))
  },

  updateOrderGroup: ({ dispatch }: any, payload: any) => {
    const { pk, ...formData } = payload
    api
      .put(`/order-group/${pk}/`, formData)
      .then(res => {
        dispatch('fetchOrderGroupList', res.data.project)
        message()
      })
      .catch(err => errorHandle(err.response.data))
  },

  deleteOrderGroup: ({ dispatch }: any, payload: any) => {
    const { pk, projId } = payload
    api
      .delete(`/order-group/${pk}/`)
      .then(() => {
        dispatch('fetchOrderGroupList', projId)
        message('danger', '알림!', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))
  },

  fetchKeyUnitList: ({ commit }: any, payload?: any) => {
    const { project } = payload
    const unit_type = payload.unit_type ? payload.unit_type : ''
    const contract = payload.contract ? payload.contract : ''
    const available = payload.available ? payload.available : 'true'
    api
      .get(
        `/key-unit/?project=${project}&unit_type=${unit_type}&contract=${contract}&available=${available}`,
      )
      .then(res => {
        commit(FETCH_KEY_UNIT_LIST, res.data)
      })
      .catch(err => errorHandle(err.response.data))
  },

  fetchHouseUnitList: ({ commit }: any, payload?: any) => {
    const { project } = payload
    let url = `/available-house-unit/?project=${project}`
    if (payload.unit_type) url += `&unit_type=${payload.unit_type}`
    if (payload.contract) url += `&contract=${payload.contract}`
    api
      .get(url)
      .then(res => {
        commit(FETCH_HOUSE_UNIT_LIST, res.data)
      })
      .catch(err => errorHandle(err.response.data))
  },

  fetchSalePriceList: ({ commit }: any, payload: any) => {
    const { project } = payload

    let url = `/price/?project=${project}`
    if (payload.order_group) url += `&order_group=${payload.order_group}`
    if (payload.unit_type) url += `&unit_type=${payload.unit_type}`

    api
      .get(url)
      .then(res => {
        commit(FETCH_SALES_PRICE_LIST, res.data)
      })
      .catch(err => errorHandle(err.response.data))
  },

  fetchDownPayList: ({ commit }: any, payload: any) => {
    const { project } = payload

    let url = `/down-payment/?project=${project}`
    if (payload.order_group) url += `&order_group=${payload.order_group}`
    if (payload.unit_type) url += `&unit_type=${payload.unit_type}`

    api
      .get(url)
      .then(res => {
        commit(FETCH_DOWN_PAYMENT_LIST, res.data)
      })
      .catch(err => errorHandle(err.response.data))
  },

  fetchContReleaseList: ({ commit }: any, payload: any) => {
    const { project } = payload
    const page = payload.page ? payload.page : 1
    const url = `/contractor-release/?project=${project}&page=${page}`
    api
      .get(url)
      .then(res => {
        commit(FETCH_CONT_RELEASE_LIST, res.data)
      })
      .catch(err => errorHandle(err.response.data))
  },

  fetchContRelease: ({ commit }: any, pk: number) => {
    api
      .get(`/contractor-release/${pk}/`)
      .then(res => {
        commit(FETCH_CONT_RELEASE, res.data)
      })
      .catch(err => errorHandle(err.response.data))
  },

  releaseSet: async ({ dispatch }: any, payload: any) => {
    const contractorId = payload.contractor

    const contractor = await api
      .get(`/contractor/${contractorId}/`)
      .then(res => res.data)
      .catch(err => errorHandle(err.response.data))

    const contractId = contractor.contract.pk
    const keyunitId = contractor.contract.keyunit

    // 1. 계약자 상태 변경
    api
      .patch(`/contractor/${contractorId}/`, {
        is_registed: false,
        status: String(Number(contractor.status) + 2),
      })
      .then(() => {
        dispatch('fetchContractor', contractorId)
      })
      .catch(err => errorHandle(err.response.data))

    // 2. 계약 상태 변경
    api
      .get(`/contract/${contractId}/`)
      .then(res => {
        api
          .patch(`/contract/${contractId}/`, {
            serial_number: `${res.data.serial_number}-terminated-${payload.completion_date}`,
            activation: false,
          })
          .then(() => dispatch('fetchContract', contractId))
          .catch(err => errorHandle(err.response.data))
      })
      .catch(err => errorHandle(err.response.data))

    // 3. 계약유닛 연결 해제
    const keyunit = await api
      .patch(`/key-unit/${keyunitId}/`, { contract: null })
      .then(res => res.data)
      .catch(err => errorHandle(err.response.data))

    // 4. 동호수 연결 해제
    if (keyunit.houseunit) {
      api
        .patch(`/house-unit/${keyunit.houseunit}/`, { key_unit: null })
        .catch(err => errorHandle(err.response.data))
    }

    // 5. 분담금 납부 상태 환불처리 // release table status -> 4로 입력될 때 1회 실행
    const payments = await api
      .get(`/project-cashbook/?contract=${contractId}`)
      .then(res => res.data)
      .catch(err => errorHandle(err.response.data))

    payments.forEach((payment: any) => {
      const append_txt = payment.note === '' ? '' : ', '
      const append_msg = payload.completion_date
        ? `${payload.completion_date} 환불건`
        : ''
      api.patch(`/project-cashbook/${payment.pk}`, {
        project_account_d2: `${payment.project_account_d1 + 63}`,
        refund_contractor: contractorId,
        note: `${payment.note}${append_txt}${append_msg}`,
      })
    })
  },

  createRelease: async ({ dispatch }: any, payload: any) => {
    // 1. 해지 정보 테이블 데이터 생성
    const { refund_amount, ...restData } = payload
    const createData = !refund_amount ? restData : payload

    api
      .post(`/contractor-release/`, createData)
      .then(res => {
        dispatch('fetchContRelease', res.data.pk)
        dispatch('fetchContReleaseList', { project: payload.project })
      })
      .catch(err => errorHandle(err.response.data))

    if (payload.status >= '4') {
      dispatch('releaseSet', payload)
    }
    message()
  },

  updateRelease: async ({ dispatch }: any, payload: any) => {
    const { pk, refund_amount, ...updateData } = payload

    api.get(`/contractor-release/${pk}/`).then(res => {
      const status = res.data.status < '4' && payload.status >= '4'
      const completion_date =
        !res.data.completion_date && payload.completion_date
      if (status || completion_date) {
        dispatch('releaseSet', payload)
      }

      // 1. 해지 정보 테이블 데이터 업데이트
      const page = payload.page
      const project = payload.project
      const fixedData =
        refund_amount !== ''
          ? { refund_amount, ...updateData }
          : { ...{ refund_amount: null }, ...updateData }
      api
        .put(`/contractor-release/${pk}/`, fixedData)
        .then(res => {
          dispatch('fetchContRelease', res.data.pk)
          dispatch('fetchContReleaseList', { project, page })
        })
        .catch(err => errorHandle(err.response.data))
    })

    message()
  },
}

export default actions
