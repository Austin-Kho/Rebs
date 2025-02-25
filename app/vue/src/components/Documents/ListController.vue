<script lang="ts" setup>
import { reactive, computed, nextTick, onBeforeMount } from 'vue'
import { useProject } from '@/store/pinia/project'
import { type DocsFilter, useDocs } from '@/store/pinia/docs'
import { numFormat } from '@/utils/baseMixins'
import { bgLight } from '@/utils/cssMixins'
import Multiselect from '@vueform/multiselect'

const props = defineProps({
  comFrom: { type: Boolean, default: false },
  getSuitCase: { type: Object, default: null },
  docsFilter: { type: Object, required: true },
})
const emit = defineEmits(['list-filter'])

const form = reactive<DocsFilter>({
  limit: '',
  company: '',
  project: '',
  is_com: props.comFrom,
  lawsuit: '',
  ordering: '-created',
  search: '',
})

const formsCheck = computed(() => {
  const a = form.limit === ''
  const b = form.is_com === !!props.comFrom
  const c = !!props.comFrom ? form.project === '' : true
  const d = !form.lawsuit
  const e = form.ordering === '-created'
  const f = form.search === ''
  return a && b && c && d && e && f
})

const docsStore = useDocs()
const docsCount = computed(() => docsStore.docsCount)

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filter', {
      ...{ page },
      ...form,
    })
  })
}

const firstSorting = (event: { target: { value: number | null } }) => {
  const val = event.target.value
  if (!val) form.is_com = props.comFrom ?? true
  else {
    form.is_com = false
    form.project = val
  }
  listFiltering(1)
}

const projectChange = (project: number | null) => (form.project = project ?? '')

const resetForm = () => {
  form.limit = ''
  form.is_com = !!props.comFrom
  form.project = ''
  form.lawsuit = ''
  form.ordering = '-created'
  form.search = ''
  listFiltering(1)
}

defineExpose({ listFiltering, projectChange, resetForm })

const projectStore = useProject()
const projSelect = computed(() => projectStore.projSelect)
const fetchProjectList = () => projectStore.fetchProjectList()
onBeforeMount(() => {
  fetchProjectList()
  if (props.docsFilter) {
    form.limit = props.docsFilter.limit
    form.company = props.docsFilter.company
    form.project = props.docsFilter.project
    form.is_com = props.docsFilter.is_com
    form.ordering = props.docsFilter.ordering
    form.search = props.docsFilter.search
    form.page = props.docsFilter.page
  }
})
</script>

<template>
  <CCallout :color="comFrom ? 'primary' : 'success'" class="pb-0 mb-4" :class="bgLight">
    <CRow>
      <CCol lg="6">
        <CRow>
          <CCol md="6" lg="4" xl="3" class="mb-3">
            <CFormSelect v-model.number="form.limit" @change="listFiltering(1)">
              <option value="">표시 개수</option>
              <option :value="10" :disabled="form.limit === '' || form.limit === 10">10 개</option>
              <option :value="30" :disabled="form.limit === 30">30 개</option>
              <option :value="50" :disabled="form.limit === 50">50 개</option>
              <!--              <option value="100">100 개</option>-->
            </CFormSelect>
          </CCol>

          <CCol v-if="comFrom" md="6" lg="4" xl="3" class="mb-3">
            <CFormSelect v-model="form.project" @change="firstSorting">
              <option value="">본사</option>
              <option v-for="proj in projSelect" :key="proj.value" :value="proj.value">
                {{ proj.label }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="6" lg="4" xl="3" class="mb-3">
            <CFormSelect v-model="form.ordering" @change="listFiltering(1)">
              <option value="created">작성일자 오름차순</option>
              <option value="-created">작성일자 내림차순</option>
              <option value="execution_date">발행일자 오름차순</option>
              <option value="-execution_date">발행일자 내림차순</option>
              <option value="-hit">조회수 오름차순</option>
              <option value="hit">조회수 내림차순</option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="6">
        <CRow class="justify-content-md-end">
          <CCol v-if="getSuitCase" md="6" lg="5" xl="3" class="mb-3">
            <Multiselect
              v-model="form.lawsuit"
              :options="getSuitCase"
              placeholder="사건번호"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              @change="listFiltering(1)"
            />
          </CCol>
          <CCol md="6" lg="5" xl="4" class="mb-3">
            <CInputGroup class="flex-nowrap">
              <CFormInput
                v-model="form.search"
                :placeholder="`제목, 내용, 첨부링크, 첨부파일명, 작성자${
                  getSuitCase ? ', 사건번호(명)' : ''
                }`"
                @keydown.enter="listFiltering(1)"
              />
              <CInputGroupText @click="listFiltering(1)">검색</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
    <CRow>
      <CCol color="warning" class="p-2 pl-3">
        <strong> 문서 건수 조회 결과 : {{ numFormat(docsCount, 0, 0) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <CButton color="info" size="sm" @click="resetForm"> 검색조건 초기화</CButton>
      </CCol>
    </CRow>
  </CCallout>
</template>
