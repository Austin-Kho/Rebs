import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createVuetify } from 'vuetify'
import CoreuiVue from '@coreui/vue'

import AppHeaderDropdownAccnt from '@/layouts/containers/AppHeaderDropdownAccnt.vue'

const vuetify = createVuetify()

describe('AppHeaderDropdownAccnt Component Test', () => {
  it('should ', async () => {
    vi.mock('vue-router', async () => {
      const actual = await vi.importActual('vue-router')
      return {
        ...(actual as object),
        useRouter: vi.fn(() => ({
          push: () => {},
        })),
      }
    })

    const wrapper = mount(AppHeaderDropdownAccnt, {
      global: {
        plugins: [createTestingPinia(), vuetify, CoreuiVue],
        mocks: {},
        provide: {},
        components: {},
        directives: {},
        stubs: ['CIcon'],
      },
      attrs: {},
      props: {
        userInfo: {
          pk: 1,
          email: 'admin@mail.com',
          username: 'admin',
          is_active: false,
          is_superuser: false,
          date_joined: '2022-01-30T19:16:53+09:00',
          staffauth: null,
          profile: null,
        },
        profile: null,
      },
      slots: {},
    })

    expect(wrapper.find('.dropdown-header').text()).toBe('admin님')

    await wrapper.setProps({
      profile: {
        pk: 1,
        user: 1,
        name: '운영자',
        birth_date: '',
        cell_phone: '',
        image: null,
        like_post: [],
        like_comment: [],
      },
    })

    expect(wrapper.find('.dropdown-header').text()).toBe('운영자님')
    expect(wrapper.find('.dropdown-menu').html()).toContain('할일 관리')
    expect(wrapper.find('.dropdown-menu').html()).toContain('프로필')
    expect(wrapper.find('.dropdown-menu').html()).not.toContain('사용자 매뉴얼')
    expect(wrapper.find('.dropdown-menu').html()).not.toContain('관리자 페이지')

    await wrapper.setProps({
      userInfo: {
        pk: 1,
        email: 'admin@mail.com',
        username: 'admin',
        is_active: true,
        is_superuser: true,
        date_joined: '2022-01-30T19:16:53+09:00',
        staffauth: null,
        profile: null,
      },
    })

    expect(wrapper.find('.dropdown-menu').html()).toContain('사용자 매뉴얼')
    expect(wrapper.find('.dropdown-menu').html()).toContain('관리자 페이지')
    expect(wrapper.find('.dropdown-menu').html()).toContain('로그아웃')
  })
})
