#!/bin/bash
# Launch Streamlit app for Swing Strategy Lab

echo "🚀 Launching Swing Strategy Lab..."
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get the project root (parent of scripts directory)
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project root
cd "$PROJECT_ROOT" || exit 1

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit is not installed"
    echo "Please install it with: pip install streamlit plotly"
    exit 1
fi

# Check if app.py exists
if [ ! -f "src/auronai/ui/app.py" ]; then
    echo "❌ Error: src/auronai/ui/app.py not found"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo "📂 Running from: $PROJECT_ROOT"
echo ""

# Launch app
streamlit run src/auronai/ui/app.py \
    --server.port 8501 \
    --server.address localhost \
    --theme.base light \
    --theme.primaryColor "#1f77b4"
