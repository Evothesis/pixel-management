#!/bin/bash
# cleanup-exposed-credentials.sh - Remove exposed credentials from git repository
#
# This script safely removes exposed credential files from the repository
# and git history to prevent ongoing security notifications.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}🚨 CREDENTIAL CLEANUP - SECURITY REMEDIATION${NC}"
echo -e "${RED}=============================================${NC}"
echo ""
echo -e "${YELLOW}This script will remove exposed credential files from:${NC}"
echo "   1. Working directory (current files)"
echo "   2. Git index (staged files)"  
echo "   3. Git history (past commits)"
echo ""

# List exposed credential files
echo -e "${YELLOW}🔍 Scanning for exposed credential files...${NC}"

CREDENTIAL_FILES=(
    "deployment-credentials-20250709-154843.txt"
    "deployment-credentials-20250709-162250.txt"
    "deployment-credentials-20250709-163158.txt"
    "deployment-credentials-20250709-184334.txt"
    "deployment-credentials-*.txt"
)

FOUND_FILES=()

for pattern in "${CREDENTIAL_FILES[@]}"; do
    if ls $pattern 1> /dev/null 2>&1; then
        for file in $pattern; do
            if [[ -f "$file" ]]; then
                FOUND_FILES+=("$file")
                echo -e "${RED}   ❌ Found: $file${NC}"
            fi
        done
    fi
done

if [ ${#FOUND_FILES[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ No credential files found in working directory${NC}"
else
    echo -e "${RED}Found ${#FOUND_FILES[@]} credential files to remove${NC}"
fi

echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  You have uncommitted changes. Please commit or stash them first.${NC}"
    echo -e "${YELLOW}   git add . && git commit -m \"Save work before credential cleanup\"${NC}"
    exit 1
fi

echo -e "${YELLOW}🧹 CLEANUP PLAN:${NC}"
echo "   1. Remove credential files from working directory"
echo "   2. Remove from git index"
echo "   3. Add comprehensive .gitignore protection"
echo "   4. Remove from git history (git filter-branch)"
echo "   5. Force push to update remote repository"
echo ""

read -p "🚨 Proceed with credential cleanup? This will modify git history! (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled"
    exit 1
fi

echo ""
echo -e "${BLUE}🧹 Starting credential cleanup...${NC}"

# Step 1: Remove credential files from working directory
echo -e "${YELLOW}Step 1: Removing credential files from working directory...${NC}"
for file in "${FOUND_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        rm -f "$file"
        echo -e "${GREEN}   ✅ Removed: $file${NC}"
    fi
done

# Also remove any other credential files that match patterns
for pattern in "deployment-credentials-*.txt" "*credentials*.txt"; do
    for file in $pattern; do
        if [[ -f "$file" && "$file" != "$pattern" ]]; then
            rm -f "$file"
            echo -e "${GREEN}   ✅ Removed: $file${NC}"
        fi
    done
done

# Step 2: Remove from git index
echo -e "${YELLOW}Step 2: Removing from git index...${NC}"
for pattern in "deployment-credentials-*.txt" "*credentials*.txt"; do
    git rm --cached "$pattern" 2>/dev/null || true
done

# Step 3: Add comprehensive .gitignore
echo -e "${YELLOW}Step 3: Adding credential protection to .gitignore...${NC}"

# Backup existing .gitignore
if [[ -f ".gitignore" ]]; then
    cp .gitignore .gitignore.backup
    echo -e "${GREEN}   ✅ Backed up existing .gitignore${NC}"
fi

# Add security protection to .gitignore
cat >> .gitignore << 'EOF'

# ============================================================================
# SECURITY: Credential Protection - NEVER COMMIT THESE FILES
# ============================================================================

# Deployment credentials (any pattern)
deployment-credentials-*.txt
*credentials*.txt
*-credentials-*.txt
evothesis-credentials-*.txt
pixel-management-credentials-*.txt

# Environment files with secrets
.env.production
.env.local
.env.staging
*.env.production
*.env.local

# Service account and API keys  
credentials.json
service-account*.json
*-service-account.json
*.pem
*.p12

# Deployment artifacts that may contain secrets
deploy-logs-*.txt
auth-test-*.txt
deployment-output-*.txt

# Backup files that may contain secrets
*.backup
*.bak
*~

# Editor files that may contain secrets
.vscode/settings.json
.idea/
*.swp
*.swo

# ============================================================================
EOF

echo -e "${GREEN}   ✅ Updated .gitignore with credential protection${NC}"

# Step 4: Remove from git history
echo -e "${YELLOW}Step 4: Removing from git history (this may take a moment)...${NC}"

# Use git filter-branch to remove credential files from all commits
git filter-branch --force --index-filter \
    'git rm --cached --ignore-unmatch deployment-credentials-*.txt *credentials*.txt' \
    --prune-empty --tag-name-filter cat -- --all

echo -e "${GREEN}   ✅ Removed from git history${NC}"

# Step 5: Commit the cleanup
echo -e "${YELLOW}Step 5: Committing cleanup changes...${NC}"
git add .gitignore
git commit -m "SECURITY: Remove exposed credentials and add protection

- Remove all deployment-credentials-*.txt files
- Add comprehensive .gitignore for credential protection  
- Prevent future credential exposure

Fixes: Generic High Entropy Secret notifications"

echo -e "${GREEN}   ✅ Committed cleanup changes${NC}"

# Step 6: Clean up refs
echo -e "${YELLOW}Step 6: Cleaning up git references...${NC}"
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo -e "${GREEN}   ✅ Cleaned up git references${NC}"

echo ""
echo -e "${GREEN}🎉 CREDENTIAL CLEANUP COMPLETED!${NC}"
echo -e "${GREEN}=================================${NC}"
echo ""
echo -e "${BLUE}✅ What was cleaned up:${NC}"
echo "   🗑️  Removed ${#FOUND_FILES[@]} credential files from working directory"
echo "   🗑️  Removed credential files from git index"
echo "   🗑️  Removed credential files from entire git history"
echo "   🛡️  Added comprehensive .gitignore protection"
echo "   📝 Committed cleanup changes"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo ""
echo "1. ${YELLOW}Force push to update remote repository:${NC}"
echo "   git push origin --force --all"
echo "   git push origin --force --tags"
echo ""
echo "2. ${YELLOW}Rotate compromised credentials:${NC}"
echo "   - Update Cloud Run environment variables"
echo "   - Generate new API keys using deployment script"
echo ""
echo "3. ${YELLOW}Verify cleanup:${NC}"
echo "   - Check that no credential files remain: ls *credentials*.txt"
echo "   - Verify .gitignore protection: git check-ignore deployment-credentials-test.txt"
echo ""
echo -e "${RED}⚠️  IMPORTANT:${NC}"
echo "   - All exposed credentials should be considered compromised"
echo "   - Force push will rewrite git history for all team members"
echo "   - Team members will need to re-clone or reset their local repos"
echo ""
echo -e "${GREEN}✅ Repository is now secure against credential exposure!${NC}"