import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/contexts/AuthContext'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { AppShell } from '@/components/AppShell'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { LoginPage } from '@/pages/LoginPage'
import { RecipesPage } from '@/pages/RecipesPage'
import { RecipeDetailPage } from '@/pages/RecipeDetailPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
})

function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter basename="/app">
          <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route index element={<RecipesPage />} />
              <Route path="recipes/:id" element={<RecipeDetailPage />} />
              <Route path="meal-plans" element={<PlaceholderPage title="Meal Plans" />} />
              <Route path="shopping-lists" element={<PlaceholderPage title="Shopping Lists" />} />
              <Route path="admin" element={<PlaceholderPage title="Admin" />} />
            </Route>
          </Routes>
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  )
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div>
      <h1 className="text-3xl font-semibold">{title}</h1>
      <p className="text-muted-foreground">Coming soon</p>
    </div>
  )
}

export default App
