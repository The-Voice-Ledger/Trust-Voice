#!/bin/bash
# Lab 5 Module Testing - Database Query Helper

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Lab 5 Module Testing - Database Helper              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠️  Loading environment variables...${NC}"
    source venv/bin/activate
    set -a
    source .env
    set +a
fi

# Function to run query and format output
run_query() {
    local title=$1
    local query=$2
    
    echo -e "\n${GREEN}▶ $title${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    psql "$DATABASE_URL" -c "$query"
    echo ""
}

# Menu
echo "Select query to run:"
echo "  1) Latest Campaigns"
echo "  2) Latest Donations"
echo "  3) Impact Verifications"
echo "  4) Campaign Verifications"
echo "  5) Campaign with Details"
echo "  6) User Registrations"
echo "  7) All Module Data (Full Report)"
echo "  8) Custom Query"
echo "  0) Exit"
echo ""
read -p "Enter choice [0-8]: " choice

case $choice in
    1)
        run_query "Latest 5 Campaigns" \
            "SELECT id, title, status, raised_amount_usd, goal_amount_usd, donor_count, verification_count, avg_trust_score, created_at FROM campaigns ORDER BY created_at DESC LIMIT 5;"
        ;;
    2)
        run_query "Latest 5 Donations" \
            "SELECT d.id, d.amount_usd, d.currency, d.status, d.payment_method, d.transaction_id, c.title as campaign, d.created_at FROM donations d LEFT JOIN campaigns c ON d.campaign_id = c.id ORDER BY d.created_at DESC LIMIT 5;"
        ;;
    3)
        run_query "Latest Impact Verifications" \
            "SELECT id, campaign_id, trust_score, status, agent_payout_status, agent_payout_amount_usd, verification_date FROM impact_verifications ORDER BY created_at DESC LIMIT 5;"
        ;;
    4)
        run_query "Campaign Verification Summary" \
            "SELECT c.title, c.status, c.verification_count, c.avg_trust_score, c.created_at FROM campaigns c WHERE c.verification_count > 0 ORDER BY c.created_at DESC LIMIT 5;"
        ;;
    5)
        read -p "Enter campaign title (partial match): " campaign_title
        run_query "Campaign: $campaign_title" \
            "SELECT c.id, c.title, c.status, c.category, c.raised_amount_usd, c.goal_amount_usd, c.donor_count, c.verification_count, c.avg_trust_score, c.location, c.beneficiaries, c.timeline, c.created_at FROM campaigns c WHERE c.title ILIKE '%$campaign_title%' ORDER BY c.created_at DESC LIMIT 3;"
        
        # Get campaign ID for related data
        campaign_id=$(psql "$DATABASE_URL" -t -c "SELECT id FROM campaigns WHERE title ILIKE '%$campaign_title%' ORDER BY created_at DESC LIMIT 1;" | xargs)
        
        if [ ! -z "$campaign_id" ]; then
            run_query "Donations for Campaign" \
                "SELECT d.amount_usd, d.currency, d.status, d.payment_method, d.created_at FROM donations d WHERE d.campaign_id = '$campaign_id' ORDER BY d.created_at DESC LIMIT 5;"
            
            run_query "Verifications for Campaign" \
                "SELECT iv.trust_score, iv.status, iv.agent_payout_status, iv.verification_date FROM impact_verifications iv WHERE iv.campaign_id = '$campaign_id' ORDER BY iv.created_at DESC LIMIT 5;"
        fi
        ;;
    6)
        run_query "User Registrations by Role" \
            "SELECT role, COUNT(*) as count FROM users GROUP BY role ORDER BY count DESC;"
        
        run_query "Recent Users" \
            "SELECT id, phone_number, role, preferred_language, is_phone_verified, created_at FROM users ORDER BY created_at DESC LIMIT 10;"
        ;;
    7)
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}                    FULL MODULE REPORT                         ${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        
        run_query "Module 1: Campaigns Created" \
            "SELECT COUNT(*) as total_campaigns, COUNT(CASE WHEN status='active' THEN 1 END) as active, COUNT(CASE WHEN status='pending' THEN 1 END) as pending FROM campaigns;"
        
        run_query "Module 1: Recent Campaigns" \
            "SELECT id, title, status, goal_amount_usd, created_at FROM campaigns ORDER BY created_at DESC LIMIT 3;"
        
        run_query "Module 2: Donations Summary" \
            "SELECT COUNT(*) as total_donations, SUM(amount_usd) as total_usd, COUNT(CASE WHEN status='completed' THEN 1 END) as completed, COUNT(CASE WHEN status='pending' THEN 1 END) as pending FROM donations;"
        
        run_query "Module 2: Recent Donations" \
            "SELECT d.amount_usd, d.status, d.payment_method, c.title as campaign FROM donations d LEFT JOIN campaigns c ON d.campaign_id = c.id ORDER BY d.created_at DESC LIMIT 3;"
        
        run_query "Module 4: Impact Reports Summary" \
            "SELECT COUNT(*) as total_reports, AVG(trust_score) as avg_trust_score, COUNT(CASE WHEN status='approved' THEN 1 END) as approved, COUNT(CASE WHEN agent_payout_status='completed' THEN 1 END) as payouts_completed FROM impact_verifications;"
        
        run_query "Module 5: Verification Summary by Campaign" \
            "SELECT c.title, c.status, c.verification_count, c.avg_trust_score FROM campaigns c WHERE c.verification_count > 0 ORDER BY c.avg_trust_score DESC LIMIT 5;"
        
        run_query "Module 7: Users by Role" \
            "SELECT role, COUNT(*) as count FROM users GROUP BY role;"
        
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        ;;
    8)
        read -p "Enter your custom SQL query: " custom_query
        run_query "Custom Query" "$custom_query"
        ;;
    0)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}✅ Query completed${NC}"
echo ""
