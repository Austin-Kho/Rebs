import { computed, h, resolveComponent } from 'vue'
import { useAccount } from '@/store/pinia/account'

const account = computed(() => useAccount())
const pageViewAuth = computed(
  () =>
    account.value.userInfo?.is_superuser ||
    (account.value.userInfo?.staffauth &&
      account.value.userInfo.staffauth?.human_resource > '0'),
)

const hrManage = {
  path: 'hr-manage',
  name: '본사 인사 관리',
  redirect: '/hr-manage/staff',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'staff',
      name: '직원 정보 관리',
      component: () =>
        pageViewAuth.value
          ? import('@/views/hrManage/Staff/Index.vue')
          : import('@/views/_Accounts/NoAuth.vue'),
      meta: { title: '직원 정보 관리', auth: true },
    },
    {
      path: 'department',
      name: '부서 정보 관리',
      component: () =>
        pageViewAuth.value
          ? import('@/views/hrManage/Department/Index.vue')
          : import('@/views/_Accounts/NoAuth.vue'),
      meta: { title: '부서 정보 관리', auth: true },
    },
    {
      path: 'position',
      name: '직위 정보 관리',
      component: () =>
        pageViewAuth.value
          ? import('@/views/hrManage/Position/Index.vue')
          : import('@/views/_Accounts/NoAuth.vue'),
      meta: { title: '직위 정보 관리', auth: true },
    },
    {
      path: 'duty',
      name: '직책 정보 관리',
      component: () =>
        pageViewAuth.value
          ? import('@/views/hrManage/Duty/Index.vue')
          : import('@/views/_Accounts/NoAuth.vue'),
      meta: { title: '직책 정보 관리', auth: true },
    },
    {
      path: 'grade',
      name: '직급 정보 관리',
      component: () =>
        pageViewAuth.value
          ? import('@/views/hrManage/Grade/Index.vue')
          : import('@/views/_Accounts/NoAuth.vue'),
      meta: { title: '직급 정보 관리', auth: true },
    },
  ],
}

export default hrManage
