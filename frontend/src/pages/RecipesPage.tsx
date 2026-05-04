import { useState } from 'react'
import { useRecipeSearch } from '@/hooks/useRecipes'
import { RecipeCard } from '@/components/RecipeCard'
import { RecipeGridSkeleton } from '@/components/RecipeSkeleton'
import type { SearchParams } from '@/types/recipe'

export function RecipesPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchParams, setSearchParams] = useState<SearchParams>({})

  const { data, isLoading, error } = useRecipeSearch(searchParams)

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearchParams({ ...searchParams, q: searchQuery || undefined })
  }

  return (
    <div>
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Recipes</h1>
          {data && (
            <p className="text-sm text-muted-foreground">
              {data.count} {data.count === 1 ? 'recipe' : 'recipes'}
            </p>
          )}
        </div>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            placeholder="Search recipes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:w-64"
          />
          <button
            type="submit"
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Search
          </button>
        </form>
      </div>

      {isLoading && <RecipeGridSkeleton count={6} />}

      {error && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-destructive">
          Failed to load recipes. Please try again.
        </div>
      )}

      {data && data.recipes.length === 0 && (
        <div className="rounded-lg border border-border bg-muted/50 p-8 text-center">
          <p className="text-lg font-medium">No recipes found</p>
          <p className="text-sm text-muted-foreground">
            {searchParams.q
              ? 'Try adjusting your search terms'
              : 'Add some recipes to get started'}
          </p>
        </div>
      )}

      {data && data.recipes.length > 0 && (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {data.recipes.map((recipe) => (
            <RecipeCard key={recipe.id} recipe={recipe} />
          ))}
        </div>
      )}
    </div>
  )
}
