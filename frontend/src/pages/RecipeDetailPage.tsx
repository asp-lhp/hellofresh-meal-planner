import { useParams, Link } from 'react-router-dom'
import { useRecipe } from '@/hooks/useRecipes'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

function formatTime(minutes: number | null): string {
  if (!minutes) return '—'
  if (minutes < 60) return `${minutes} min`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
}

export function RecipeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const recipeId = parseInt(id || '0', 10)
  const { data: recipe, isLoading, error } = useRecipe(recipeId)

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 w-48 rounded bg-muted" />
        <div className="mt-4 aspect-video w-full max-w-2xl rounded-lg bg-muted" />
        <div className="mt-6 h-4 w-full max-w-lg rounded bg-muted" />
        <div className="mt-2 h-4 w-3/4 max-w-lg rounded bg-muted" />
      </div>
    )
  }

  if (error || !recipe) {
    return (
      <div className="text-center">
        <h1 className="text-2xl font-semibold">Recipe not found</h1>
        <p className="mt-2 text-muted-foreground">
          The recipe you're looking for doesn't exist.
        </p>
        <Link
          to="/"
          className="mt-4 inline-block text-primary hover:underline"
        >
          ← Back to recipes
        </Link>
      </div>
    )
  }

  return (
    <div>
      <Link
        to="/"
        className="mb-4 inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
      >
        ← Back to recipes
      </Link>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <h1 className="text-3xl font-bold">{recipe.name}</h1>

          {recipe.description && (
            <p className="mt-2 text-lg text-muted-foreground">
              {recipe.description}
            </p>
          )}

          {recipe.imageUrl && (
            <div className="mt-6 overflow-hidden rounded-lg">
              <img
                src={recipe.imageUrl}
                alt={recipe.name}
                className="aspect-video w-full object-cover"
              />
            </div>
          )}

          <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatBox label="Prep Time" value={formatTime(recipe.prepTime)} />
            <StatBox label="Cook Time" value={formatTime(recipe.cookTime)} />
            <StatBox label="Total Time" value={formatTime(recipe.totalTime)} />
            <StatBox label="Servings" value={recipe.servings?.toString() || '—'} />
          </div>

          {recipe.difficulty && (
            <div className="mt-4">
              <Badge variant="default">{recipe.difficulty}</Badge>
            </div>
          )}

          {(recipe.calories || recipe.protein || recipe.carbs || recipe.fat) && (
            <Card className="mt-6">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Nutrition per serving</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  {recipe.calories && (
                    <NutritionItem label="Calories" value={recipe.calories} unit="kcal" />
                  )}
                  {recipe.protein && (
                    <NutritionItem label="Protein" value={recipe.protein} unit="g" />
                  )}
                  {recipe.carbs && (
                    <NutritionItem label="Carbs" value={recipe.carbs} unit="g" />
                  )}
                  {recipe.fat && (
                    <NutritionItem label="Fat" value={recipe.fat} unit="g" />
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {recipe.tags.length > 0 && (
            <div className="mt-6">
              <h2 className="text-sm font-medium text-muted-foreground">Tags</h2>
              <div className="mt-2 flex flex-wrap gap-2">
                {recipe.tags.map((tag) => (
                  <Badge key={tag.id} variant="secondary">
                    {tag.tagName}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {recipe.allergens.length > 0 && (
            <div className="mt-4">
              <h2 className="text-sm font-medium text-muted-foreground">Allergens</h2>
              <div className="mt-2 flex flex-wrap gap-2">
                {recipe.allergens.map((allergen) => (
                  <Badge key={allergen.id} variant="destructive">
                    ⚠️ {allergen.allergenName}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <div className="mt-8">
            <h2 className="text-xl font-semibold">Instructions</h2>
            {recipe.instructions.length > 0 ? (
              <ol className="mt-4 space-y-6">
                {recipe.instructions
                  .sort((a, b) => a.stepNumber - b.stepNumber)
                  .map((instruction) => (
                    <li key={instruction.id} className="flex flex-col gap-3 sm:flex-row sm:gap-4">
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground">
                        {instruction.stepNumber}
                      </span>
                      <div className="flex-1">
                        {instruction.description && (
                          <p className="text-foreground">{instruction.description}</p>
                        )}
                        {instruction.imageUrl && (
                          <img
                            src={instruction.imageUrl}
                            alt={`Step ${instruction.stepNumber}`}
                            className="mt-2 max-w-md rounded-lg"
                          />
                        )}
                        {!instruction.description && !instruction.imageUrl && (
                          <p className="text-muted-foreground italic">See image</p>
                        )}
                      </div>
                    </li>
                  ))}
              </ol>
            ) : (
              <p className="mt-4 text-muted-foreground">No instructions available.</p>
            )}
          </div>
        </div>

        <div>
          <Card className="sticky top-20">
            <CardHeader>
              <CardTitle>Ingredients</CardTitle>
            </CardHeader>
            <CardContent>
              {recipe.ingredients.length > 0 ? (
                <ul className="space-y-2">
                  {recipe.ingredients
                    .sort((a, b) => a.order - b.order)
                    .map((ingredient) => (
                      <li
                        key={ingredient.id}
                        className="flex items-start gap-2 border-b border-border pb-2 last:border-0"
                      >
                        <span className="text-foreground">
                          {ingredient.quantity && (
                            <span className="font-medium">
                              {ingredient.quantity}
                              {ingredient.unit && ` ${ingredient.unit}`}
                            </span>
                          )}{' '}
                          {ingredient.name}
                          {ingredient.notes && (
                            <span className="text-sm text-muted-foreground">
                              {' '}
                              ({ingredient.notes})
                            </span>
                          )}
                        </span>
                      </li>
                    ))}
                </ul>
              ) : (
                <p className="text-muted-foreground">No ingredients listed.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-card p-3 text-center">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  )
}

function NutritionItem({
  label,
  value,
  unit,
}: {
  label: string
  value: number
  unit: string
}) {
  return (
    <div>
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold">
        {value}
        <span className="text-sm font-normal text-muted-foreground"> {unit}</span>
      </p>
    </div>
  )
}
