<template>
  <div class="container mx-auto p-4">
    <div class="hero min-h-screen">
      <div class="hero-content text-center">
        <div class="max-w-md">
          <h1 class="text-5xl font-bold">Invoice OCR</h1>
          <p class="py-6">Thai Invoice Processing System with LINE Integration</p>

          <div class="card bg-base-200 shadow-xl">
            <div class="card-body">
              <h2 class="card-title">System Health</h2>

              <div class="stats stats-vertical shadow">
                <div class="stat">
                  <div class="stat-title">API Service</div>
                  <div class="stat-value text-sm" :class="apiHealth.status === 'healthy' ? 'text-success' : 'text-error'">
                    {{ apiHealth.status || 'checking...' }}
                  </div>
                </div>

                <div class="stat">
                  <div class="stat-title">OCR Service</div>
                  <div class="stat-value text-sm" :class="ocrHealth.status === 'healthy' ? 'text-success' : 'text-error'">
                    {{ ocrHealth.status || 'checking...' }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const apiHealth = ref<any>({})
const ocrHealth = ref<any>({})

const checkHealth = async () => {
  try {
    const apiResponse = await axios.get('http://localhost:3000/health')
    apiHealth.value = apiResponse.data
  } catch (error) {
    apiHealth.value = { status: 'unhealthy' }
  }

  try {
    const ocrResponse = await axios.get('http://localhost:8001/health')
    ocrHealth.value = ocrResponse.data
  } catch (error) {
    ocrHealth.value = { status: 'unhealthy' }
  }
}

onMounted(() => {
  checkHealth()
  setInterval(checkHealth, 5000)
})
</script>