import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { createRouter, createWebHashHistory } from 'vue-router'
import { start, close } from '@/utils/nprogress'
import routes from '@/router/routes'
import store from '@/store'

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const isAuth = computed(() => useAccount().isAuthorized)
  if (
    !isAuth.value &&
    !(
      to.name === 'Login' ||
      to.name === 'Register' ||
      to.name === 'RegisterCode'
    )
  )
    next({ name: 'Login', query: { redirect: to.fullPath } })

  start()
  store.commit('startSpinner')
  next()
})

router.afterEach(() => {
  store.commit('endSpinner')
  close()
})

export default router
