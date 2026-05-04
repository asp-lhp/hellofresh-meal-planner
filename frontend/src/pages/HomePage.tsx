import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function HomePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Dashboard</h1>
        <p className="text-muted-foreground">Welcome to your meal planner</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Recipes</CardTitle>
            <CardDescription>Browse your recipe collection</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-primary">—</p>
            <p className="text-sm text-muted-foreground">Total recipes</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Meal Plans</CardTitle>
            <CardDescription>Your weekly meal plans</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-primary">—</p>
            <p className="text-sm text-muted-foreground">Active plans</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Shopping Lists</CardTitle>
            <CardDescription>Grocery lists ready for Kroger</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-primary">—</p>
            <p className="text-sm text-muted-foreground">Pending items</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
