/* eslint-disable no-unused-vars */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  full_name: string
  role: string
}

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: User | null
  isAuthenticated: boolean
  login: (accessToken: string, refreshToken: string, user: User) => void
  logout: () => void
  updateUser: (user: User) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      login: (_accessToken, _refreshToken, _user) =>
        set({
          accessToken: _accessToken,
          refreshToken: _refreshToken,
          user: _user,
          isAuthenticated: true,
        }),
      logout: () =>
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        }),
      updateUser: (_user) => set({ user: _user }),
    }),
    {
      name: 'ehazop-auth',
    }
  )
)

// WebSocket connection store
interface WSState {
  connected: boolean
  connect: (_studyId: string, _token: string) => void
  disconnect: () => void
  updatePresence: (_presence: Record<string, any>) => void
  updateLocks: (_locks: Record<string, string>) => void
}

export const useWSStore = create<WSState>((set) => ({
  connected: false,
  connect: (_studyId, _token) => set({ connected: true }),
  disconnect: () => set({ connected: false }),
  updatePresence: (_presence) => set((state) => ({ ...state })),
  updateLocks: (_locks) => set((state) => ({ ...state })),
}))