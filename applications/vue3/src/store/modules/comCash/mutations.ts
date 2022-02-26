import {
  FETCH_ACC_SORT_LIST,
  FETCH_CASHBOOK_LIST,
  FETCH_FORM_ACC_D1_LIST,
  FETCH_FORM_ACC_D2_LIST,
  FETCH_FORM_ACC_D3_LIST,
  FETCH_ACC_D1_LIST,
  FETCH_ACC_D2_LIST,
  FETCH_ACC_D3_LIST,
  FETCH_COMPAY_BANK_LIST,
} from '@/store/modules/comCash/mutations-types'
import { CashesState } from '@/store/modules/comCash/state'

const mutations = {
  [FETCH_ACC_SORT_LIST]: (state: CashesState, payload: any) =>
    (state.sortList = payload.results),

  [FETCH_ACC_D1_LIST]: (state: CashesState, payload: any) =>
    (state.listAccD1List = payload.results),

  [FETCH_ACC_D2_LIST]: (state: CashesState, payload: any) =>
    (state.listAccD2List = payload.results),

  [FETCH_ACC_D3_LIST]: (state: CashesState, payload: any) =>
    (state.listAccD3List = payload.results),

  [FETCH_FORM_ACC_D1_LIST]: (state: CashesState, payload: any) =>
    (state.formAccD1List = payload.results),

  [FETCH_FORM_ACC_D2_LIST]: (state: CashesState, payload: any) =>
    (state.formAccD2List = payload.results),

  [FETCH_FORM_ACC_D3_LIST]: (state: CashesState, payload: any) =>
    (state.formAccD3List = payload.results),

  [FETCH_COMPAY_BANK_LIST]: (state: CashesState, payload: any) =>
    (state.comBankList = payload.results),

  [FETCH_CASHBOOK_LIST]: (state: CashesState, payload: any) => {
    state.cashBookList = payload.results
    state.cashBookCount = payload.count
  },
}

export default mutations
