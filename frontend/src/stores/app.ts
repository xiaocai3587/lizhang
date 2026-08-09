// 全局应用状态
import { ref } from 'vue';

const loading = ref(false);
const currentPersonId = ref<string | null>(null);

export function useApp() {
  function setLoading(val: boolean) {
    loading.value = val;
  }

  function setCurrentPerson(id: string | null) {
    currentPersonId.value = id;
  }

  return { loading, currentPersonId, setLoading, setCurrentPerson };
}
