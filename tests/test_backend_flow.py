"""
Backend Flow Tests - Check if API endpoints are working
"""
import sys
import json
import time
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed. Install with: pip install requests")
    sys.exit(1)

BASE_URL = "http://localhost:8080"

def test_endpoint(method, url, description, timeout=5, **kwargs):
    """Test an API endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"URL: {method} {url}")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, timeout=timeout, **kwargs)
        elif method == "POST":
            response = requests.post(url, timeout=timeout, **kwargs)
        else:
            print(f"  ✗ Unsupported method: {method}")
            return False
        
        elapsed = time.time() - start_time
        
        print(f"  Status: {response.status_code}")
        print(f"  Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  ✓ Response OK")
                
                # Show key fields
                if isinstance(data, dict):
                    for key in ['status', 'version', 'location', 'risk_score', 'type', 'features']:
                        if key in data:
                            value = data[key]
                            if isinstance(value, (list, dict)):
                                print(f"  → {key}: {type(value).__name__} ({len(value) if hasattr(value, '__len__') else 'N/A'})")
                            else:
                                print(f"  → {key}: {value}")
                
                return True
            except json.JSONDecodeError:
                print(f"  ⚠ Response is not JSON")
                print(f"  Content: {response.text[:200]}")
                return False
        else:
            print(f"  ✗ Error response: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Error detail: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"  Error text: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"  ✗ TIMEOUT (> {timeout}s)")
        return False
    except requests.exceptions.ConnectionError:
        print(f"  ✗ CONNECTION ERROR - Is backend running?")
        return False
    except Exception as e:
        print(f"  ✗ ERROR: {type(e).__name__}: {e}")
        return False

def main():
    """Run all backend flow tests"""
    print("="*60)
    print("BACKEND FLOW TESTS")
    print("="*60)
    
    results = []
    
    # 1. Root endpoint
    results.append(("Root", test_endpoint("GET", f"{BASE_URL}/", "Root endpoint")))
    
    # 2. Health check
    results.append(("Health", test_endpoint("GET", f"{BASE_URL}/api/analysis/health", "Health check")))
    
    # 3. Analyze endpoint (GET)
    results.append(("Analyze (GET)", test_endpoint(
        "GET", 
        f"{BASE_URL}/api/analysis/analyze?location=Miami", 
        "Analyze endpoint (GET) - Miami",
        timeout=15
    )))
    
    # 4. Analyze endpoint (POST) - with timeout
    results.append(("Analyze (POST)", test_endpoint(
        "POST",
        f"{BASE_URL}/api/analysis/analyze",
        "Analyze endpoint (POST) - Miami",
        json={"location": "Miami"},
        timeout=15
    )))
    
    # 5. Risk-map endpoint
    results.append(("Risk Map", test_endpoint(
        "GET",
        f"{BASE_URL}/api/analysis/risk-map?city=Miami&resolution=8",
        "Risk-map endpoint - Miami",
        timeout=15
    )))
    
    # 6. Professional analysis endpoint
    results.append(("Professional", test_endpoint(
        "GET",
        f"{BASE_URL}/api/analysis/professional?city=Miami",
        "Professional analysis endpoint - Miami",
        timeout=20
    )))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All backend endpoints working!")
        return 0
    elif passed >= total * 0.5:
        print("\n⚠ Some endpoints have issues. Check logs above.")
        return 1
    else:
        print("\n✗ Most endpoints failing. Check backend logs and dependencies.")
        return 2

if __name__ == "__main__":
    sys.exit(main())
