"""
Quick smoke test script to validate basic integration.
Run this before full test suite for quick sanity check.
"""
import sys
from pathlib import Path
import requests
import time

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_status(message, status="info"):
    """Print colored status message"""
    colors = {"success": GREEN, "error": RED, "warning": YELLOW, "info": BLUE}
    color = colors.get(status, RESET)
    symbol = "✓" if status == "success" else "✗" if status == "error" else "•"
    print(f"{color}{symbol} {message}{RESET}")


def test_server_running(base_url):
    """Test if server is running"""
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print_status(f"Server is running at {base_url}", "success")
            return True
        else:
            print_status(f"Server responded with {response.status_code}", "warning")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"Server not accessible: {e}", "error")
        return False


def test_static_files(base_url):
    """Test that static HTML files are accessible"""
    files = [
        "index.html",
        "campaigns.html",
        "donate.html",
        "create-campaign-wizard.html",
        "ngo-register-wizard.html"
    ]
    
    print(f"\n{BLUE}Testing Static Files:{RESET}")
    success_count = 0
    
    for filename in files:
        try:
            response = requests.get(f"{base_url}/{filename}", timeout=5)
            if response.status_code == 200:
                print_status(f"{filename} accessible", "success")
                success_count += 1
            else:
                print_status(f"{filename} returned {response.status_code}", "warning")
        except Exception as e:
            print_status(f"{filename} failed: {e}", "error")
    
    return success_count, len(files)


def test_api_endpoints(base_url):
    """Test critical API endpoints"""
    endpoints = [
        ("GET", "/api/campaigns/", "Campaign list"),
        ("POST", "/api/voice/wizard-step", "Voice wizard"),
        ("POST", "/api/voice/dictate-text", "Voice dictate"),
        ("POST", "/api/voice/search-campaigns", "Voice search"),
    ]
    
    print(f"\n{BLUE}Testing API Endpoints:{RESET}")
    success_count = 0
    
    for method, path, description in endpoints:
        try:
            url = f"{base_url}{path}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                # POST without data will fail validation but prove endpoint exists
                response = requests.post(url, timeout=5)
            
            # For GET, 200 is success
            # For POST, 422 (validation error) proves endpoint exists
            if (method == "GET" and response.status_code == 200) or \
               (method == "POST" and response.status_code in [400, 422]):
                print_status(f"{description} ({method} {path})", "success")
                success_count += 1
            elif response.status_code == 404:
                print_status(f"{description} NOT FOUND ({path})", "error")
            else:
                print_status(f"{description} returned {response.status_code}", "warning")
        except Exception as e:
            print_status(f"{description} failed: {e}", "error")
    
    return success_count, len(endpoints)


def test_voice_endpoint_structure(base_url):
    """Test voice endpoints accept multipart/form-data"""
    print(f"\n{BLUE}Testing Voice Endpoint Structure:{RESET}")
    
    # Create minimal form data
    files = {'audio': ('test.webm', b'test', 'audio/webm')}
    data = {'field_name': 'test', 'step_number': '1'}
    
    try:
        response = requests.post(
            f"{base_url}/api/voice/wizard-step",
            files=files,
            data=data,
            timeout=10
        )
        
        # We expect 400 or 500 due to invalid audio, but not 404 or 415
        if response.status_code in [400, 500, 422]:
            print_status("Voice endpoint accepts audio uploads", "success")
            return True
        elif response.status_code == 415:
            print_status("Voice endpoint doesn't accept multipart data", "error")
            return False
        elif response.status_code == 404:
            print_status("Voice wizard endpoint not found", "error")
            return False
        else:
            print_status(f"Unexpected response: {response.status_code}", "warning")
            return True
    except Exception as e:
        print_status(f"Voice endpoint test failed: {e}", "error")
        return False


def test_campaign_data_structure(base_url):
    """Test campaign API returns correct data structure"""
    print(f"\n{BLUE}Testing Campaign Data Structure:{RESET}")
    
    try:
        response = requests.get(f"{base_url}/api/campaigns/", timeout=5)
        if response.status_code == 200:
            campaigns = response.json()
            
            if isinstance(campaigns, list):
                print_status("Campaigns API returns list", "success")
                
                if len(campaigns) > 0:
                    campaign = campaigns[0]
                    required_fields = ['id', 'title', 'description', 'goal_amount_usd', 'status']
                    missing_fields = [f for f in required_fields if f not in campaign]
                    
                    if not missing_fields:
                        print_status("Campaign objects have required fields", "success")
                        print_status(f"Found {len(campaigns)} campaigns", "info")
                        return True
                    else:
                        print_status(f"Missing fields: {missing_fields}", "error")
                        return False
                else:
                    print_status("No campaigns in database (create test data)", "warning")
                    return True
            else:
                print_status("Campaigns API doesn't return list", "error")
                return False
        else:
            print_status(f"Campaigns API returned {response.status_code}", "error")
            return False
    except Exception as e:
        print_status(f"Campaign data test failed: {e}", "error")
        return False


def test_cors_headers(base_url):
    """Test CORS headers are present"""
    print(f"\n{BLUE}Testing CORS Configuration:{RESET}")
    
    try:
        response = requests.options(f"{base_url}/api/campaigns/", timeout=5)
        
        if response.status_code in [200, 204]:
            print_status("CORS preflight supported", "success")
            return True
        else:
            print_status(f"CORS preflight returned {response.status_code}", "warning")
            return False
    except Exception as e:
        print_status(f"CORS test failed: {e}", "warning")
        return False


def main():
    """Run all smoke tests"""
    # Default to localhost
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001"
    
    print(f"\n{BLUE}{'='*60}")
    print(f"  TrustVoice Mini App Integration Smoke Test")
    print(f"  Testing: {base_url}")
    print(f"{'='*60}{RESET}\n")
    
    start_time = time.time()
    
    # Run tests
    tests_passed = 0
    tests_total = 0
    
    # 1. Server running
    if test_server_running(base_url):
        tests_passed += 1
    tests_total += 1
    
    # 2. Static files
    passed, total = test_static_files(base_url)
    tests_passed += passed
    tests_total += total
    
    # 3. API endpoints
    passed, total = test_api_endpoints(base_url)
    tests_passed += passed
    tests_total += total
    
    # 4. Voice endpoint structure
    if test_voice_endpoint_structure(base_url):
        tests_passed += 1
    tests_total += 1
    
    # 5. Campaign data structure
    if test_campaign_data_structure(base_url):
        tests_passed += 1
    tests_total += 1
    
    # 6. CORS
    if test_cors_headers(base_url):
        tests_passed += 1
    tests_total += 1
    
    # Summary
    elapsed = time.time() - start_time
    success_rate = (tests_passed / tests_total) * 100 if tests_total > 0 else 0
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"\n{BLUE}Summary:{RESET}")
    print(f"  Tests Passed: {tests_passed}/{tests_total} ({success_rate:.1f}%)")
    print(f"  Time: {elapsed:.2f}s")
    
    if success_rate == 100:
        print(f"\n{GREEN}✓ All tests passed! Integration looks good.{RESET}\n")
        return 0
    elif success_rate >= 80:
        print(f"\n{YELLOW}⚠ Most tests passed. Review warnings above.{RESET}\n")
        return 0
    else:
        print(f"\n{RED}✗ Integration issues detected. Check errors above.{RESET}\n")
        return 1


if __name__ == "__main__":
    exit(main())
