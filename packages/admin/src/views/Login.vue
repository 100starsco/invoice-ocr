<template>
  <div class="min-h-screen bg-base-200 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <div class="card bg-base-100 shadow-2xl">
        <div class="card-body">
          <!-- Header -->
          <div class="text-center mb-8">
            <h1 class="text-4xl font-bold text-primary mb-2">Invoice OCR</h1>
            <h2 class="text-xl font-semibold text-base-content">Admin Dashboard</h2>
            <p class="text-base-content/60 mt-2">Sign in to manage your system</p>
          </div>

          <!-- Login Form -->
          <form @submit.prevent="handleLogin" class="space-y-6">
            <!-- Error Alert -->
            <div v-if="authStore.error" class="alert alert-error shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{{ authStore.error }}</span>
            </div>

            <!-- Email Field -->
            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">Email Address</span>
              </label>
              <div class="relative">
                <input
                  v-model="email"
                  type="email"
                  placeholder="Enter your email"
                  class="input input-bordered w-full"
                  :class="{
                    'input-error': emailError,
                    'input-success': email && !emailError
                  }"
                  required
                  @blur="validateEmail"
                  @input="clearEmailError"
                />
                <div v-if="email && !emailError" class="absolute inset-y-0 right-0 flex items-center pr-3">
                  <svg class="h-5 w-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                </div>
              </div>
              <label v-if="emailError" class="label">
                <span class="label-text-alt text-error">{{ emailError }}</span>
              </label>
            </div>

            <!-- Password Field -->
            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">Password</span>
              </label>
              <div class="relative">
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="Enter your password"
                  class="input input-bordered w-full pr-12"
                  :class="{
                    'input-error': passwordError,
                    'input-success': password && !passwordError
                  }"
                  required
                  @blur="validatePassword"
                  @input="clearPasswordError"
                />
                <button
                  type="button"
                  class="absolute inset-y-0 right-0 flex items-center pr-3"
                  @click="togglePasswordVisibility"
                >
                  <svg v-if="showPassword" class="h-5 w-5 text-base-content/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"></path>
                  </svg>
                  <svg v-else class="h-5 w-5 text-base-content/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                  </svg>
                </button>
              </div>
              <label v-if="passwordError" class="label">
                <span class="label-text-alt text-error">{{ passwordError }}</span>
              </label>
            </div>

            <!-- Remember Me -->
            <div class="form-control">
              <label class="label cursor-pointer justify-start space-x-3">
                <input v-model="rememberMe" type="checkbox" class="checkbox checkbox-primary" />
                <span class="label-text">Remember me for 30 days</span>
              </label>
            </div>

            <!-- Submit Button -->
            <button
              type="submit"
              class="btn btn-primary w-full"
              :class="{ 'btn-disabled': !isFormValid }"
              :disabled="authStore.isLoading || !isFormValid"
            >
              <span v-if="authStore.isLoading" class="loading loading-spinner loading-sm"></span>
              {{ authStore.isLoading ? 'Signing in...' : 'Sign In' }}
            </button>
          </form>

          <!-- Divider -->
          <div class="divider my-8">Demo Credentials</div>

          <!-- Demo Info -->
          <div class="bg-base-200 rounded-lg p-4">
            <div class="text-center space-y-2">
              <p class="text-sm font-medium text-base-content">Demo Account</p>
              <div class="space-y-1 text-sm text-base-content/70">
                <p><span class="font-mono bg-base-300 px-2 py-1 rounded">admin@example.com</span></p>
                <p><span class="font-mono bg-base-300 px-2 py-1 rounded">admin123</span></p>
              </div>
              <button
                type="button"
                class="btn btn-outline btn-sm mt-3"
                @click="fillDemoCredentials"
              >
                Use Demo Credentials
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="text-center mt-6 text-base-content/60">
        <p class="text-sm">© 2024 Invoice OCR System. All rights reserved.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// Form data
const email = ref('')
const password = ref('')
const rememberMe = ref(false)
const showPassword = ref(false)

// Validation errors
const emailError = ref('')
const passwordError = ref('')

// Computed properties
const isFormValid = computed(() => {
  return email.value && password.value && !emailError.value && !passwordError.value
})

// Methods
function validateEmail() {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!email.value) {
    emailError.value = 'Email is required'
  } else if (!emailRegex.test(email.value)) {
    emailError.value = 'Please enter a valid email address'
  } else {
    emailError.value = ''
  }
}

function validatePassword() {
  if (!password.value) {
    passwordError.value = 'Password is required'
  } else if (password.value.length < 6) {
    passwordError.value = 'Password must be at least 6 characters'
  } else {
    passwordError.value = ''
  }
}

function clearEmailError() {
  if (emailError.value) {
    emailError.value = ''
  }
}

function clearPasswordError() {
  if (passwordError.value) {
    passwordError.value = ''
  }
}

function togglePasswordVisibility() {
  showPassword.value = !showPassword.value
}

function fillDemoCredentials() {
  email.value = 'admin@example.com'
  password.value = 'admin123'
  emailError.value = ''
  passwordError.value = ''
}

async function handleLogin() {
  // Validate form
  validateEmail()
  validatePassword()

  if (!isFormValid.value) return

  // Attempt login
  const success = await authStore.login(email.value, password.value)

  if (success) {
    // Redirect to intended page or dashboard
    const redirect = route.query.redirect as string || '/'
    router.push(redirect)
  }
}
</script>