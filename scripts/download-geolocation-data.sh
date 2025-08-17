#!/bin/bash

# Download DB-IP geolocation data for local development
# This script downloads the database once and stores it locally

set -e

DATA_DIR="./data/geolocation"
DB_FILE="$DATA_DIR/dbip-city-lite.csv.gz"
METADATA_FILE="$DATA_DIR/download_info.json"

# Create data directory
mkdir -p "$DATA_DIR"

# Function to get current month's URL
get_db_url() {
    local year=$(date +%Y)
    local month=$(date +%m)
    echo "https://download.db-ip.com/free/dbip-city-lite-$year-$month.csv.gz"
}

# Function to get previous month's URL (fallback)
get_prev_month_url() {
    local date=$(date -d "last month" "+%Y-%m" 2>/dev/null || date -j -v-1m "+%Y-%m")
    echo "https://download.db-ip.com/free/dbip-city-lite-$date.csv.gz"
}

# Check if data already exists and is recent (less than 30 days old)
if [[ -f "$DB_FILE" && -f "$METADATA_FILE" ]]; then
    # Check file age
    if [[ -n "$(find "$DB_FILE" -mtime -30 2>/dev/null)" ]]; then
        echo "✅ Geolocation data is recent (less than 30 days old)"
        echo "📁 Location: $DB_FILE"
        echo "📊 Size: $(du -h "$DB_FILE" | cut -f1)"
        
        # Show metadata if available
        if command -v jq >/dev/null 2>&1 && [[ -f "$METADATA_FILE" ]]; then
            echo "ℹ️  Downloaded: $(jq -r '.download_date' "$METADATA_FILE")"
            echo "🔗 Source: $(jq -r '.source_url' "$METADATA_FILE")"
        fi
        
        echo "🚀 Use existing data or delete '$DB_FILE' to re-download"
        exit 0
    else
        echo "⚠️  Geolocation data is older than 30 days, downloading fresh data..."
    fi
else
    echo "📥 Downloading DB-IP geolocation database..."
fi

# Try current month first, then previous month
urls=("$(get_db_url)" "$(get_prev_month_url)")

for url in "${urls[@]}"; do
    echo "🌐 Trying: $url"
    
    if curl -f -L --connect-timeout 10 --max-time 300 \
            --progress-bar \
            -o "$DB_FILE.tmp" \
            "$url"; then
        
        # Move successful download
        mv "$DB_FILE.tmp" "$DB_FILE"
        
        # Create metadata file
        cat > "$METADATA_FILE" << EOF
{
  "source_url": "$url",
  "download_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "file_size_bytes": $(stat -f%z "$DB_FILE" 2>/dev/null || stat -c%s "$DB_FILE"),
  "file_size_human": "$(du -h "$DB_FILE" | cut -f1)"
}
EOF
        
        echo "✅ Download successful!"
        echo "📁 Location: $DB_FILE"
        echo "📊 Size: $(du -h "$DB_FILE" | cut -f1)"
        echo "🔗 Source: $url"
        
        exit 0
    else
        echo "❌ Failed to download from $url"
        # Clean up failed download
        rm -f "$DB_FILE.tmp"
    fi
done

echo "💥 Failed to download from all URLs"
echo "🛠️  You can manually download from https://db-ip.com/db/lite.php"
echo "📝 Save as: $DB_FILE"
exit 1