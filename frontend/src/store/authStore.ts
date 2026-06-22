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
      login: (accessToken, refreshToken, user) =>
        set({
          accessToken,
          refreshToken,
          user,
          isAuthenticated: true,
        }),
      logout: () =>
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        }),
      updateUser: (user) => set({ user }),
    }),
    {
      name: 'ehazop-auth',
    }
  )
)

// WebSocket connection store
interface WSState {
  connected: boolean
  studyId: string | null
  presence: Record<string, any>
  locks: Record<string, string>
  connect: (studyId: string, token: string) => void
  disconnect: () => void
  updatePresence: (presence: Record<string, any>) => void
  updateLocks: (locks: Record<string, string>) => void
}

export const useWSStore = create<WSState>((set) => ({
  connected: false,
  studyId: null,
  presence: {},
  locks: {},
  connect: (studyId, _token) => set({ connected: true, studyId }),
  disconnect: () => set({ connected: false, studyId: null, presence: {}, locks: {} }),
  updatePresence: (presence) => set({ presence }),
  updateLocks: (locks) => set({ locks }),
}))