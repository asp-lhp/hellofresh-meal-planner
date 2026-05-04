export interface Recipe {
  id: number
  name: string
  description: string | null
  imageUrl: string | null
  totalTime: number | null
  calories: number | null
  difficulty: string | null
  servings: number
  prepTime: number | null
  cookTime: number | null
  protein: number | null
  carbs: number | null
  fat: number | null
}

export interface Ingredient {
  id: number
  recipeId: number
  name: string
  quantity: number | null
  unit: string | null
  notes: string | null
  order: number
}

export interface Instruction {
  id: number
  recipeId: number
  stepNumber: number
  description: string
  imageUrl: string | null
}

export interface Tag {
  id: number
  recipeId: number
  tagName: string
}

export interface Allergen {
  id: number
  recipeId: number
  allergenName: string
}

export interface RecipeDetail extends Recipe {
  ingredients: Ingredient[]
  instructions: Instruction[]
  tags: Tag[]
  allergens: Allergen[]
}

export interface SearchParams {
  q?: string
  difficulty?: string
  maxTime?: number
  maxCalories?: number
  tags?: string[]
}

export interface SearchFilters {
  q: string | null
  difficulty: string | null
  maxTime: number | null
  maxCalories: number | null
  tags: string[] | null
}

export interface SearchResult {
  filters: SearchFilters
  count: number
  recipes: Recipe[]
}
