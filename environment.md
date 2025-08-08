# Environment Setup (macOS, zsh)

This project uses a single notebook (`Init-JSON-data.ipynb`) to generate synthetic supply-chain JSONL files and optionally import them into MongoDB using PyMongo.

## Prerequisites
- Python 3.9+ (tested with 3.11)
- VS Code with Python and Jupyter extensions
- Optional: MongoDB (local via Homebrew) or MongoDB Atlas

## Create and activate a virtual environment
```zsh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## Install dependencies
Minimal runtime dependencies:
```zsh
pip install "pymongo>=4.6,<5"
```
Optional (quality of life):
```zsh
pip install python-dotenv
```

If you prefer a requirements file, create `requirements.txt` with:
```
pymongo>=4.6,<5
python-dotenv>=1.0,<2  # optional
```
Then install with:
```zsh
pip install -r requirements.txt
```

## Configure MongoDB (optional)
The notebook can import the generated JSONL via PyMongo. Set environment variables in your shell (or add them to `~/.zshrc`):
```zsh
export MONGO_URI="mongodb://localhost:27017"
export MONGO_DB="supply_chain_demo"
```

### Local MongoDB using Homebrew (optional)
```zsh
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

## Run the notebook
1. Open `Init-JSON-data.ipynb` in VS Code.
2. Select the `.venv` interpreter as the Jupyter kernel.
3. Run all cells.

Outputs:
- Four JSONL files are written to `../data/supply_chain/` relative to the notebook directory:
  - `products.jsonl`
  - `daily_demand.jsonl`
  - `inventory_levels.jsonl`
  - `reorder_recommendations.jsonl`

Note: Because the path is `../data/supply_chain`, the data is created one directory above this project folder. Ensure you have write permissions there.

## Import data into MongoDB (two options)
- In-notebook: Run the optional PyMongo cell at the bottom of the notebook (drops and recreates collections, inserts documents, and creates indexes).
- CLI (mongoimport), example:
```zsh
mongoimport --uri "$MONGO_URI/$MONGO_DB" \
  --collection products --file ../data/supply_chain/products.jsonl --type json --jsonArray=false
```
Repeat for the other files/collections (`daily_demand`, `inventory_levels`, `reorder_recommendations`).

## Troubleshooting
- Module not found (pymongo): Ensure the venv is active and `pip install -r requirements.txt` (or the direct install) succeeded.
- Permission denied writing data: Verify write access to the parent directory and that `../data/supply_chain` exists (the notebook creates it automatically).
- MongoDB connection errors: Make sure MongoDB is running locally or that your Atlas URI is correct and accessible.
