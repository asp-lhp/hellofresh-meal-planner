/**
 * Walmart Cart Auto-Fill Bookmarklet
 * Usage: Copy this to browser console while on walmart.com
 * Or create as a bookmarklet
 */

const SHOPPING_LIST = [
  { name: "tilapia", searchTerm: "Great Value Frozen Tilapia Fillets 2 lb", qty: 1 },
  { name: "chili flakes", searchTerm: "Great Value Crushed Red Pepper 1.75 oz", qty: 1 },
  { name: "cilantro", searchTerm: "Fresh Cilantro Bunch", qty: 1 },
  { name: "cumin", searchTerm: "Great Value Ground Cumin", qty: 1 },
  { name: "ginger", searchTerm: "Fresh Ginger Root", qty: 1 },
  { name: "israeli couscous", searchTerm: "Pearl Couscous", qty: 1 },
  { name: "lime", searchTerm: "Fresh Limes", qty: 2 },
  { name: "mini cucumber", searchTerm: "Persian Cucumbers", qty: 2 },
  { name: "radishes", searchTerm: "Fresh Radishes Bunch", qty: 2 },
  { name: "ranch steak", searchTerm: "Beef Ranch Steak", qty: 1 },
  { name: "scallions", searchTerm: "Green Onions Bunch", qty: 2 },
  { name: "sesame seeds", searchTerm: "McCormick Sesame Seed", qty: 1 },
  { name: "spicy mayo", searchTerm: "Kewpie Mayo", qty: 1 },
  { name: "sweet soy glaze", searchTerm: "Kikkoman Teriyaki Sauce", qty: 1 },
  { name: "veggie stock concentrate", searchTerm: "Better Than Bouillon Vegetable Base", qty: 1 },
  { name: "zucchini", searchTerm: "Fresh Zucchini", qty: 1 },
  { name: "rice", searchTerm: "Great Value Long Grain White Rice", qty: 1 },
  { name: "sugar", searchTerm: "Great Value Granulated Sugar", qty: 1 },
  { name: "carrot", searchTerm: "Fresh Carrots 2 lb Bag", qty: 1 },
  { name: "garlic", searchTerm: "Fresh Garlic Bulb", qty: 3 },
  { name: "onion", searchTerm: "Yellow Onion", qty: 1 }
];

async function addItemsToCart() {
  console.log("🛒 Starting Walmart Cart Fill...");
  console.log(`📋 ${SHOPPING_LIST.length} items to add\n`);

  const results = {
    added: [],
    failed: [],
    skipped: []
  };

  for (let i = 0; i < SHOPPING_LIST.length; i++) {
    const item = SHOPPING_LIST[i];
    console.log(`[${i + 1}/${SHOPPING_LIST.length}] Searching: ${item.searchTerm}...`);

    try {
      // Open search in new tab (you'll manually add to cart)
      const searchUrl = `https://www.walmart.com/search?q=${encodeURIComponent(item.searchTerm)}`;
      console.log(`   → ${searchUrl}`);

      // Wait for user to add item
      const added = confirm(`Did you add "${item.name}" to cart?\n\nSearch: ${item.searchTerm}\nQty: ${item.qty}\n\nClick OK when added, Cancel to skip`);

      if (added) {
        results.added.push(item.name);
        console.log(`   ✅ Added: ${item.name}`);
      } else {
        results.skipped.push(item.name);
        console.log(`   ⏭️  Skipped: ${item.name}`);
      }

    } catch (error) {
      results.failed.push({ name: item.name, error: error.message });
      console.error(`   ❌ Failed: ${item.name}`, error);
    }

    // Pause between items
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  // Summary
  console.log("\n📊 Summary:");
  console.log(`✅ Added: ${results.added.length}`);
  console.log(`⏭️  Skipped: ${results.skipped.length}`);
  console.log(`❌ Failed: ${results.failed.length}`);

  if (results.skipped.length > 0) {
    console.log("\nSkipped items:", results.skipped.join(", "));
  }

  if (results.failed.length > 0) {
    console.log("\nFailed items:", results.failed.map(f => f.name).join(", "));
  }
}

// Export for use
console.log("Walmart Auto-Fill Ready!");
console.log("Run: addItemsToCart()");
