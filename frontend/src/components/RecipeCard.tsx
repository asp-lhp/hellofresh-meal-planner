import { Link } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Recipe } from '@/types/recipe'

interface RecipeCardProps {
  recipe: Recipe
}

function truncate(text: string | null, maxLength: number): string {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength).trim() + '…'
}

function formatTime(minutes: number | null): string | null {
  if (!minutes) return null
  if (minutes < 60) return `${minutes} min`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
}

export function RecipeCard({ recipe }: RecipeCardProps) {
  const isQuick = recipe.totalTime && recipe.totalTime <= 30
  const timeDisplay = formatTime(recipe.totalTime)

  return (
    <Link to={`/recipes/${recipe.id}`} className="group">
      <Card className="overflow-hidden transition-shadow hover:shadow-md">
        <div className="aspect-video w-full overflow-hidden bg-muted">
          {recipe.imageUrl ? (
            <img
              src={recipe.imageUrl}
              alt={recipe.name}
              className="h-full w-full object-cover transition-transform group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-4xl text-muted-foreground">
              🍽️
            </div>
          )}
        </div>
        <CardContent className="p-4">
          <h3 className="font-semibold leading-tight text-foreground group-hover:text-primary">
            {recipe.name}
          </h3>
          {recipe.description && (
            <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
              {truncate(recipe.description, 100)}
            </p>
          )}
          <div className="mt-3 flex items-center gap-3 text-sm text-muted-foreground">
            {timeDisplay && (
              <span className="flex items-center gap-1">
                <span>⏱️</span>
                {timeDisplay}
              </span>
            )}
            {recipe.servings > 0 && (
              <span className="flex items-center gap-1">
                <span>👥</span>
                {recipe.servings}
              </span>
            )}
          </div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {recipe.difficulty && (
              <Badge variant="default" className="text-xs">
                {recipe.difficulty}
              </Badge>
            )}
            {isQuick && (
              <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100 text-xs">
                Quick
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
