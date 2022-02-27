import api from '@/api'
import {
  FETCH_P_ACC_SORT_LIST,
  FETCH_ALL_ACC_D1_LIST,
  FETCH_ALL_ACC_D2_LIST,
  FETCH_FORM_ACC_D1_LIST,
  FETCH_FORM_ACC_D2_LIST,
  FETCH_P_BANK_ACCOUNT_LIST,
  FETCH_P_CASHBOOK_LIST,
} from '@/store/modules/proCash/mutations-types'
import { message } from '@/utils/helper'

const actions = {
  fetchAccSortList: ({ commit }: any) => {
    api
      .get(`/account-sort/`)
      .then(res => {
        commit(FETCH_P_ACC_SORT_LIST, res.data)
      })
      .catch(err => console.log(err.response.data))
  },

  fetchProAllAccD1List: ({ commit }: any) => {
    api
      .get(`/project-account-depth1/`)
      .then(res => {
        commit(FETCH_ALL_ACC_D1_LIST, res.data)
      })
      .catch(err => console.log(err.response.data))
  },

  fetchProAllAccD2List: ({ commit }: any) => {
    api
      .get(`/project-account-depth2/`)
      .then(res => {
        commit(FETCH_ALL_ACC_D2_LIST, res.data)
      })
      .catch(err => console.log(err.response.data))
  },

  fetchProFormAccD1List: ({ commit }: any, sort?: string) => {
    const url = sort
      ? `/project-account-depth1/?sort=${sort}`
      : `/project-account-depth1/`
    api
      .get(url)
      .then(res => {
        commit(FETCH_FORM_ACC_D1_LIST, res.data)
      })
      .catch(err => console.log(err.response.data))
  },

  fetchProFormAccD2List: ({ commit }: any, payload?: any) => {
    const d1 = payload && payload.d1 ? payload.d1 : ''
    const sort = payload && payload.sort ? payload.sort : ''
    const url = `/project-account-depth2/?d1=${d1}&d1__sort=${sort}`
    api
      .get(url)
      .then(res => {
        commit(FETCH_FORM_ACC_D2_LIST, res.data)
      })
      .catch(err => console.log(err.response.data))
  },

  fetchProjectBankAccountList: ({ commit }: any, project: any) => {
    api
      .get(`/project-bank-account/?project=${project}`)
      .then(res => {
        commit(FETCH_P_BANK_ACCOUNT_LIST, res.data)
      })
      .catch(err => console.log(err.response.data))
  },

  createProjectBankAccount: ({ dispatch }: any, payload: any) => {
    api
      .post(`/project-bank-account/`, payload)
      .then(res => {
        dispatch('fetchProjectBankAccountList', res.data.project)
        message()
      })
      .catch(err => console.log(err.response.data))
  },

  updateProjectBankAccount: ({ dispatch }: any, payload: any) => {
    const { pk, ...formData } = payload
    api
      .put(`/project-bank-account/${pk}/`, formData)
      .then(res => {
        dispatch('fetchProjectBankAccountList', res.data.project)
        message()
      })
      .catch(err => console.log(err.response.data))
  },

  deleteProjectBankAccount: ({ dispatch }: any, payload: any) => {
    const { pk, project } = payload
    api
      .delete(`/project-bank-account/${pk}/`)
      .then(() => {
        dispatch('fetchProjectBankAccountList', project)
        message('danger', '알림!', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => console.log(err.response.data))
  },

  fetchProjectCashList: ({ commit }: any, payload: any) => {
    const { project } = payload
    let url = `/project-cashbook/?project=${project}`
    if (payload.from_date) url += `&from_deal_date=${payload.from_date}`
    if (payload.to_date) url += `&to_deal_date=${payload.to_date}`
    if (payload.sort) url += `&sort=${payload.sort}`
    if (payload.accountD1) url += `&project_account_d1=${payload.accountD1}`
    if (payload.accountD2) url += `&project_account_d2=${payload.accountD2}`
    if (payload.bank_account) url += `&bank_account=${payload.bank_account}`
    if (payload.search) url += `&search=${payload.search}`
    const page = payload.page ? payload.page : 1
    if (payload.page) url += `&page=${page}`
    api
      .get(url)
      .then(res => {
        commit(FETCH_P_CASHBOOK_LIST, res.data)
      })
      .catch(err => console.log(err.response.data))
  },

  createPrCashBook: ({ dispatch }: any, payload: any) => {
    api
      .post(`/project-cashbook/`, payload)
      .then(res => {
        dispatch('fetchProjectCashList', { project: res.data.project })
        message()
      })
      .catch(err => console.log(err.response.data))
  },

  updatePrCashBook: ({ dispatch }: any, payload: any) => {
    const { pk, page, ...formData } = payload
    api
      .put(`/project-cashbook/${pk}/`, formData)
      .then(res => {
        dispatch('fetchProjectCashList', { project: res.data.project, page })
        message()
      })
      .catch(err => console.log(err.response.data))
  },

  deletePrCashBook: ({ dispatch }: any, payload: any) => {
    const { pk, page, project } = payload
    api
      .delete(`/project-cashbook/${pk}/`)
      .then(() => {
        dispatch('fetchProjectCashList', { project, page })
        message('danger', '알림!', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => console.log(err.response.data))
  },
}

export default actions
