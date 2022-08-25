import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useType = defineStore('type', () => {
  // states

  const unitTypeList = ref([])
  const floorTypeList = ref([])

  return {
    unitTypeList,
    floorTypeList,
  }
})
