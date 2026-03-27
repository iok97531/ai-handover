import { create } from 'zustand'
import type { Project } from '../types'
import * as api from '../api/client'

interface ProjectState {
  projects: Project[]
  selectedProjectId: string | null
  loading: boolean
  error: string | null

  fetchProjects: () => Promise<void>
  addProject: (name: string, folderPath: string) => Promise<void>
  removeProject: (id: string) => Promise<void>
  selectProject: (id: string | null) => void
  triggerIndex: (id: string) => Promise<void>
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  selectedProjectId: null,
  loading: false,
  error: null,

  fetchProjects: async () => {
    set({ loading: true, error: null })
    try {
      const projects = await api.getProjects()
      set({ projects, loading: false })
    } catch (err) {
      set({ error: (err as Error).message, loading: false })
    }
  },

  addProject: async (name, folderPath) => {
    try {
      const project = await api.createProject(name, folderPath)
      set((state) => ({ projects: [...state.projects, project] }))
      // Auto-trigger indexing and update status locally
      await api.triggerIndex(project.id)
      set((state) => ({
        projects: state.projects.map((p) =>
          p.id === project.id ? { ...p, status: 'indexing' as const } : p
        )
      }))
    } catch (err) {
      set({ error: (err as Error).message })
    }
  },

  removeProject: async (id) => {
    try {
      await api.deleteProject(id)
      set((state) => ({
        projects: state.projects.filter((p) => p.id !== id),
        selectedProjectId: state.selectedProjectId === id ? null : state.selectedProjectId
      }))
    } catch (err) {
      set({ error: (err as Error).message })
    }
  },

  selectProject: (id) => set({ selectedProjectId: id }),

  triggerIndex: async (id) => {
    try {
      await api.triggerIndex(id)
    } catch (err) {
      set({ error: (err as Error).message })
    }
  }
}))
