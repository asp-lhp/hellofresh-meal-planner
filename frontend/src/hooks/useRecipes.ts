import { useQuery } from '@tanstack/react-query'
import { fetchRecipes, fetchRecipe, searchRecipes } from '@/lib/api'
import type { SearchParams } from '@/types/recipe'

export function useRecipes() {
  return useQuery({
    queryKey: ['recipes'],
    queryFn: fetchRecipes,
  })
}

export function useRecipe(id: number) {
  return useQuery({
    queryKey: ['recipe', id],
    queryFn: () => fetchRecipe(id),
    enabled: id > 0,
  })
}

export function useRecipeSearch(params: SearchParams) {
  return useQuery({
    queryKey: ['recipes', 'search', params],
    queryFn: () => searchRecipes(params),
  })
}
