import { Card, CardContent } from '@/components/ui/card'

export function RecipeSkeleton() {
  return (
    <Card className="overflow-hidden">
      <div className="aspect-video w-full animate-pulse bg-muted" />
      <CardContent className="p-4">
        <div className="h-5 w-3/4 animate-pulse rounded bg-muted" />
        <div className="mt-2 h-4 w-full animate-pulse rounded bg-muted" />
        <div className="mt-1 h-4 w-2/3 animate-pulse rounded bg-muted" />
        <div className="mt-3 flex gap-3">
          <div className="h-4 w-16 animate-pulse rounded bg-muted" />
          <div className="h-4 w-12 animate-pulse rounded bg-muted" />
        </div>
        <div className="mt-3 flex gap-1.5">
          <div className="h-5 w-14 animate-pulse rounded-full bg-muted" />
          <div className="h-5 w-12 animate-pulse rounded-full bg-muted" />
        </div>
      </CardContent>
    </Card>
  )
}

export function RecipeGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <RecipeSkeleton key={i} />
      ))}
    </div>
  )
}
