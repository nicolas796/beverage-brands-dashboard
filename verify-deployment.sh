#!/bin/bash
# Verification script for Render deployment package
# Run this to check if everything is ready for deployment

echo "=== Beverage Brands Dashboard - Deployment Verification ==="
echo ""

ERRORS=0
WARNINGS=0

# Check required files
echo "Checking required files..."

required_files=(
    "render.yaml"
    "Dockerfile"
    ".env.example"
    "DEPLOY.md"
    "README.md"
    ".gitignore"
    "backend/app.py"
    "backend/requirements.txt"
    "backend/models.py"
    "backend/database.py"
    "frontend/package.json"
    "frontend/src/utils/api.js"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file MISSING!"
        ((ERRORS++))
    fi
done

echo ""
echo "Checking environment files are gitignored..."

if grep -q "\.env" .gitignore 2>/dev/null; then
    echo "  ✓ .env files are gitignored"
else
    echo "  ✗ .env files NOT gitignored - SECURITY RISK!"
    ((ERRORS++))
fi

echo ""
echo "Checking for hardcoded secrets..."

# Check for common secret patterns in committed files
secret_patterns=(
    "sk-.*[a-zA-Z0-9]{20,}"  # API keys
    "password.*=.*['\"][^'\"]+['\"]"  # Hardcoded passwords
    "secret.*=.*['\"][^'\"]+['\"]"  # Hardcoded secrets
)

# Only check specific files (not node_modules, etc.)
files_to_check=$(find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.yaml" -o -name "*.yml" \) ! -path "*/node_modules/*" ! -path "*/venv/*" ! -path "*/__pycache__/*" 2>/dev/null)

POTENTIAL_SECRETS=0
for file in $files_to_check; do
    # Skip .env.example as it contains example values
    if [[ "$file" == *".env.example"* ]]; then
        continue
    fi
    
    # Check for suspicious patterns
    if grep -E "(password|secret|key|token).*=['\"][^'\"]{8,}['\"]" "$file" 2>/dev/null | grep -v "^#" | grep -v "getenv\|environ\|os.getenv" > /dev/null; then
        echo "  ⚠ Potential hardcoded secret in: $file"
        ((POTENTIAL_SECRETS++))
    fi
done

if [ $POTENTIAL_SECRETS -eq 0 ]; then
    echo "  ✓ No obvious hardcoded secrets found"
else
    echo "  ⚠ Found $POTENTIAL_SECRETS potential issues - review manually"
    ((WARNINGS++))
fi

echo ""
echo "Checking render.yaml validity..."

if [ -f "render.yaml" ]; then
    # Basic YAML syntax check
    if python3 -c "import yaml; yaml.safe_load(open('render.yaml'))" 2>/dev/null; then
        echo "  ✓ render.yaml is valid YAML"
    else
        echo "  ✗ render.yaml has YAML syntax errors"
        ((ERRORS++))
    fi
    
    # Check for required sections
    if grep -q "services:" render.yaml; then
        echo "  ✓ Has services section"
    else
        echo "  ✗ Missing services section"
        ((ERRORS++))
    fi
    
    if grep -q "healthCheckPath" render.yaml; then
        echo "  ✓ Has health check configured"
    else
        echo "  ⚠ No health check configured"
        ((WARNINGS++))
    fi
    
    if grep -q "disk:" render.yaml; then
        echo "  ✓ Has persistent disk configured"
    else
        echo "  ⚠ No persistent disk configured"
        ((WARNINGS++))
    fi
else
    echo "  ✗ render.yaml not found"
    ((ERRORS++))
fi

echo ""
echo "Checking Dockerfile..."

if [ -f "Dockerfile" ]; then
    if grep -q "FROM" Dockerfile; then
        echo "  ✓ Dockerfile has base image"
    else
        echo "  ✗ Dockerfile missing base image"
        ((ERRORS++))
    fi
    
    if grep -q "EXPOSE 8000" Dockerfile; then
        echo "  ✓ Exposes port 8000"
    else
        echo "  ⚠ Should expose port 8000"
        ((WARNINGS++))
    fi
else
    echo "  ✗ Dockerfile not found"
    ((ERRORS++))
fi

echo ""
echo "Checking backend dependencies..."

if [ -f "backend/requirements.txt" ]; then
    required_packages=("fastapi" "uvicorn" "sqlalchemy")
    for pkg in "${required_packages[@]}"; do
        if grep -qi "$pkg" backend/requirements.txt; then
            echo "  ✓ Has $pkg"
        else
            echo "  ✗ Missing $pkg"
            ((ERRORS++))
        fi
    done
else
    echo "  ✗ requirements.txt not found"
    ((ERRORS++))
fi

echo ""
echo "Checking frontend..."

if [ -f "frontend/package.json" ]; then
    if grep -q '"react"' frontend/package.json; then
        echo "  ✓ React dependency found"
    else
        echo "  ✗ React not in dependencies"
        ((ERRORS++))
    fi
    
    if grep -q '"build"' frontend/package.json; then
        echo "  ✓ Build script defined"
    else
        echo "  ✗ Build script missing"
        ((ERRORS++))
    fi
else
    echo "  ✗ package.json not found"
    ((ERRORS++))
fi

echo ""
echo "Checking documentation..."

if [ -f "DEPLOY.md" ]; then
    if grep -q "Environment Variables" DEPLOY.md; then
        echo "  ✓ DEPLOY.md has env var documentation"
    else
        echo "  ⚠ DEPLOY.md missing env var docs"
        ((WARNINGS++))
    fi
else
    echo "  ✗ DEPLOY.md not found"
    ((ERRORS++))
fi

echo ""
echo "=== Verification Complete ==="
echo ""
echo "Results:"
echo "  Errors: $ERRORS"
echo "  Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "✅ Package is ready for deployment!"
    if [ $WARNINGS -gt 0 ]; then
        echo "⚠️  Address $WARNINGS warning(s) for optimal setup."
    fi
    exit 0
else
    echo "❌ Fix $ERRORS error(s) before deploying."
    exit 1
fi
