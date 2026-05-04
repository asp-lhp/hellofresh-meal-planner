# OpenClaw Integration

Scripts and configuration for automating grocery ordering with OpenClaw.

## Setup

1. Install OpenClaw: https://openclaw.ai
2. Configure Amazon Fresh credentials
3. Copy `shopping-list-template.json` and customize

## Usage

The API outputs shopping lists in OpenClaw-compatible JSON format.

OpenClaw will:
1. Read the shopping list
2. Navigate to Amazon Fresh
3. Search for each ingredient
4. Apply smart substitutions (upgrade quality, max 2x price)
5. Add items to cart
6. (Optionally) Complete checkout
