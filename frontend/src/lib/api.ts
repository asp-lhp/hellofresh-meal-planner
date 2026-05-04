import type { Recipe, RecipeDetail, SearchParams, SearchResult } from '@/types/recipe'

const API_BASE = '/api'

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }
  return response.json()
}

export async function fetchRecipes(): Promise<Recipe[]> {
  return fetchJson<Recipe[]>(`${API_BASE}/recipes`)
}

export async function fetchRecipe(id: number): Promise<RecipeDetail> {
  return fetchJson<RecipeDetail>(`${API_BASE}/recipes/${id}`)
}

export async function searchRecipes(params: SearchParams): Promise<SearchResult> {
  const searchParams = new URLSearchParams()

  if (params.q) searchParams.set('q', params.q)
  if (params.difficulty) searchParams.set('difficulty', params.difficulty)
  if (params.maxTime) searchParams.set('maxTime', params.maxTime.toString())
  if (params.maxCalories) searchParams.set('maxCalories', params.maxCalories.toString())
  if (params.tags?.length) {
    params.tags.forEach(tag => searchParams.append('tags', tag))
  }

  const queryString = searchParams.toString()
  const url = queryString
    ? `${API_BASE}/recipes/search?${queryString}`
    : `${API_BASE}/recipes/search`

  return fetchJson<SearchResult>(url)
}

export async function fetchStats(): Promise<{ recipes: number }> {
  return fetchJson<{ recipes: number }>(`${API_BASE}/stats`)
}
