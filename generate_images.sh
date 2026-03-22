#!/bin/bash

echo "=========================================="
echo "NASCAR AI Strategy Engine"
echo "Generating README Visualization Images"
echo "=========================================="
echo ""

# Check if kaleido is installed
python -c "import kaleido" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing kaleido for image generation..."
    pip install kaleido
fi

# Create images directory
mkdir -p docs/images

# Run the image generation script
echo "Generating images..."
python generate_readme_images.py

echo ""
echo "=========================================="
echo "Complete! Images saved to docs/images/"
echo "=========================================="
echo ""
echo "Images generated:"
echo "  ✓ strategy_comparison.png"
echo "  ✓ sensitivity_analysis.png"
echo "  ✓ position_distribution.png"
echo "  ✓ performance_metrics.png"
echo "  ✓ tire_degradation.png"
echo "  ✓ roi_analysis.png"
echo ""
echo "These images are now referenced in README.md"
