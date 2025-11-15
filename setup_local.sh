#!/bin/bash

echo "🚀 Setting up local development environment for ForkU..."
echo ""

# Check if Postgres is installed
if ! command -v psql &> /dev/null; then
    echo "⚠️  Postgres not found."
    echo "   Install with: brew install postgresql"
    echo "   Or download Postgres.app from: https://postgresapp.com/"
    echo ""
else
    echo "✓ Postgres found: $(psql --version)"
fi

# Check if Postgres is running
if command -v psql &> /dev/null; then
    if psql -l &> /dev/null; then
        echo "✓ Postgres is running"
    else
        echo "⚠️  Postgres may not be running"
        echo "   Start with: brew services start postgresql"
        echo "   Or start Postgres.app"
    fi
fi

# Create database
if command -v createdb &> /dev/null; then
    echo ""
    echo "Creating database 'forku_db'..."
    createdb forku_db 2>/dev/null && echo "✓ Database created" || echo "⚠️  Database may already exist (that's okay)"
fi

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo ""
    echo "⚠️  AWS CLI not found."
    echo "   Install with: brew install awscli"
    echo "   Or download from: https://aws.amazon.com/cli/"
else
    echo ""
    echo "✓ AWS CLI found: $(aws --version)"
    echo "   Configure with: aws configure"
fi

# Check Python dependencies
echo ""
echo "Checking Python dependencies..."
if [ -f "requirements.txt" ]; then
    echo "✓ requirements.txt found"
    echo "   Install with: pip install -r requirements.txt"
else
    echo "⚠️  requirements.txt not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Setup check complete!"
echo ""
echo "Next steps:"
echo "1. Create .env file (see .env.example or SETUP_GUIDE.md)"
echo "2. Set up AWS credentials and S3 buckets"
echo "3. Install Python dependencies: pip install -r requirements.txt"
echo "4. Test connections:"
echo "   - python test_db.py"
echo "   - python test_s3.py"
echo ""
echo "See SETUP_GUIDE.md for detailed instructions."

