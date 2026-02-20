import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginUser, registerUser, getMe } from '../services/api'
import router from '../router'

const TOKEN_KEY = 'token'

export const useAuthStore = defineStore('auth', () => {
  // ── State ────────────────────────────────────────────────────────────────────
  const token = ref(localStorage.getItem(TOKEN_KEY))
  const user = ref(null)

  // ── Getters ──────────────────────────────────────────────────────────────────
  const isAuthenticated = computed(() => !!token.value)

  // ── Helpers ──────────────────────────────────────────────────────────────────
  function saveToken(t) {
    token.value = t
    localStorage.setItem(TOKEN_KEY, t)
  }

  function clearToken() {
    token.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  async function fetchCurrentUser() {
    const res = await getMe()
    user.value = res.data
  }

  // ── Actions ──────────────────────────────────────────────────────────────────
  async function login(email, password) {
    const res = await loginUser(email, password)
    saveToken(res.data.access_token)
    await fetchCurrentUser()
  }

  async function register(email, username, password) {
    await registerUser(email, username, password)
    await login(email, password)
  }

  function loginWithGoogle() {
    window.location.href = '/api/auth/google'
  }

  async function handleGoogleCallback(newToken) {
    saveToken(newToken)
    await fetchCurrentUser()
  }

  function logout() {
    clearToken()
    user.value = null
    router.push('/login')
  }

  async function checkAuth() {
    if (!token.value) return
    try {
      await fetchCurrentUser()
    } catch (err) {
      if (err.response?.status === 401) {
        logout()
      }
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    login,
    register,
    loginWithGoogle,
    handleGoogleCallback,
    logout,
    checkAuth,
  }
})
