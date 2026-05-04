// Meal Planner Navigation & State Management
// Unified navigation component for all meal planning pages

class MealPlannerState {
    constructor() {
        this.storageKey = 'mealPlannerState';
        this.loadState();
    }

    loadState() {
        const saved = localStorage.getItem(this.storageKey);
        if (saved) {
            this.state = JSON.parse(saved);
        } else {
            this.state = {
                currentMealPlanId: 1,
                currentWeekStart: '2026-03-24',
                currentWeekEnd: '2026-03-28',
                weekLabel: 'March 24-28',
                history: []
            };
            this.saveState();
        }
    }

    saveState() {
        localStorage.setItem(this.storageKey, JSON.stringify(this.state));
    }

    setCurrentMealPlan(planId, weekStart, weekEnd, label) {
        this.state.currentMealPlanId = planId;
        this.state.currentWeekStart = weekStart;
        this.state.currentWeekEnd = weekEnd;
        this.state.weekLabel = label;
        this.saveState();
        this.updateNavigationUI();
    }

    getCurrentMealPlan() {
        return {
            id: this.state.currentMealPlanId,
            weekStart: this.state.currentWeekStart,
            weekEnd: this.state.currentWeekEnd,
            label: this.state.weekLabel
        };
    }

    updateNavigationUI() {
        const weekDisplay = document.getElementById('current-week-display');
        if (weekDisplay) {
            weekDisplay.textContent = this.state.weekLabel;
        }
    }
}

// Global state instance
const mealPlannerState = new MealPlannerState();

// Navigation Component
function createNavigation() {
    const nav = document.createElement('nav');
    nav.className = 'meal-planner-nav';

    const currentPlan = mealPlannerState.getCurrentMealPlan();

    nav.innerHTML = `
        <div class="nav-container">
            <div class="nav-brand">
                <span class="nav-icon">🍽️</span>
                <span class="nav-title">Meal Planner</span>
            </div>

            <div class="nav-week-selector">
                <label for="week-select">Week:</label>
                <select id="week-select" class="week-dropdown">
                    <option value="1" ${currentPlan.id === 1 ? 'selected' : ''}>March 24-28 (Current)</option>
                    <option value="2" ${currentPlan.id === 2 ? 'selected' : ''}>March 31 - April 4 (Next Week)</option>
                    <option value="3" ${currentPlan.id === 3 ? 'selected' : ''}>April 7-11 (Plan Ahead)</option>
                </select>
                <span id="current-week-display" class="week-badge">${currentPlan.label}</span>
            </div>

            <div class="nav-links">
                <a href="index.html" class="nav-link">
                    <span class="link-icon">🏠</span>
                    <span>Home</span>
                </a>
                <a href="weeknight-recipes.html" class="nav-link">
                    <span class="link-icon">📖</span>
                    <span>Recipes</span>
                </a>
                <a href="complete-shopping-list-mon-fri.html" class="nav-link">
                    <span class="link-icon">🛒</span>
                    <span>Shopping List</span>
                </a>
                <a href="meal-prep-guide.html" class="nav-link">
                    <span class="link-icon">🥘</span>
                    <span>Meal Prep</span>
                </a>
                <a href="quick-cook-guide.html" class="nav-link">
                    <span class="link-icon">⚡</span>
                    <span>Quick Cook</span>
                </a>
            </div>
        </div>
    `;

    return nav;
}

// Navigation Styles
function injectNavigationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .meal-planner-nav {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            gap: 30px;
            flex-wrap: wrap;
        }

        .nav-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 22px;
            font-weight: 700;
        }

        .nav-icon {
            font-size: 28px;
        }

        .nav-week-selector {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(255,255,255,0.1);
            padding: 8px 15px;
            border-radius: 8px;
            flex-grow: 1;
            max-width: 400px;
        }

        .nav-week-selector label {
            font-weight: 600;
            font-size: 14px;
        }

        .week-dropdown {
            padding: 6px 12px;
            border-radius: 6px;
            border: none;
            background: white;
            color: #333;
            font-size: 14px;
            cursor: pointer;
            flex: 1;
        }

        .week-badge {
            background: rgba(255,255,255,0.2);
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            white-space: nowrap;
        }

        .nav-links {
            display: flex;
            gap: 5px;
            margin-left: auto;
        }

        .nav-link {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 8px 14px;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            text-decoration: none;
            color: white;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }

        .nav-link:hover {
            background: rgba(255,255,255,0.25);
            transform: translateY(-2px);
        }

        .link-icon {
            font-size: 18px;
        }

        @media (max-width: 900px) {
            .nav-container {
                gap: 15px;
            }

            .nav-week-selector {
                flex-grow: 0;
                max-width: 100%;
            }

            .nav-links {
                width: 100%;
                justify-content: space-between;
                margin-left: 0;
            }

            .nav-link span:not(.link-icon) {
                display: none;
            }

            .nav-link {
                padding: 8px 12px;
            }
        }

        @media print {
            .meal-planner-nav {
                display: none;
            }
        }
    `;
    document.head.appendChild(style);
}

// Initialize navigation on page load
function initMealPlannerNavigation() {
    injectNavigationStyles();
    const nav = createNavigation();

    // Insert navigation at the beginning of body
    if (document.body.firstChild) {
        document.body.insertBefore(nav, document.body.firstChild);
    } else {
        document.body.appendChild(nav);
    }

    // Add event listener for week selector
    const weekSelect = document.getElementById('week-select');
    if (weekSelect) {
        weekSelect.addEventListener('change', function() {
            const planId = parseInt(this.value);
            let weekStart, weekEnd, label;

            switch(planId) {
                case 1:
                    weekStart = '2026-03-24';
                    weekEnd = '2026-03-28';
                    label = 'March 24-28';
                    break;
                case 2:
                    weekStart = '2026-03-31';
                    weekEnd = '2026-04-04';
                    label = 'March 31 - April 4';
                    break;
                case 3:
                    weekStart = '2026-04-07';
                    weekEnd = '2026-04-11';
                    label = 'April 7-11';
                    break;
            }

            mealPlannerState.setCurrentMealPlan(planId, weekStart, weekEnd, label);
        });
    }

    // Highlight current page in navigation
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-link').forEach(link => {
        const linkPage = link.getAttribute('href');
        if (linkPage === currentPage || (currentPage === '' && linkPage === 'index.html')) {
            link.style.background = 'rgba(255,255,255,0.3)';
            link.style.fontWeight = '700';
        }
    });
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMealPlannerNavigation);
} else {
    initMealPlannerNavigation();
}
