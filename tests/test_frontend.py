"""
Frontend validation tests - checks structure and configuration
"""
import sys
from pathlib import Path
import json

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def test_frontend_structure():
    """Test frontend directory structure"""
    frontend_path = Path(__file__).parent.parent / "app" / "frontend"
    
    print("Testing frontend structure...")
    
    # Check required files
    required_files = [
        "package.json",
        "index.html",
        "vite.config.js",
        "src/main.jsx",
        "src/App.jsx",
        "src/styles/global.css"
    ]
    
    missing = []
    for file in required_files:
        path = frontend_path / file
        if not path.exists():
            missing.append(file)
        else:
            print(f"  ✓ {file}")
    
    if missing:
        print(f"  ✗ Missing files: {missing}")
        return False
    
    return True

def test_package_json():
    """Test package.json configuration"""
    frontend_path = Path(__file__).parent.parent / "app" / "frontend"
    package_json = frontend_path / "package.json"
    
    print("\nTesting package.json...")
    
    try:
        with open(package_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check required dependencies
        deps = data.get('dependencies', {})
        required_deps = ['react', 'react-dom', 'maplibre-gl']
        
        missing_deps = []
        for dep in required_deps:
            if dep not in deps:
                missing_deps.append(dep)
            else:
                print(f"  ✓ {dep}: {deps[dep]}")
        
        if missing_deps:
            print(f"  ✗ Missing dependencies: {missing_deps}")
            return False
        
        # Check scripts
        scripts = data.get('scripts', {})
        if 'dev' not in scripts:
            print("  ✗ Missing 'dev' script")
            return False
        print(f"  ✓ dev script: {scripts['dev']}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error reading package.json: {e}")
        return False

def test_components():
    """Test component files exist"""
    frontend_path = Path(__file__).parent.parent / "app" / "frontend"
    components_path = frontend_path / "src" / "components"
    
    print("\nTesting components...")
    
    required_components = [
        "ProfessionalPanel.jsx",
        "TimelineSlider.jsx",
        "ExportButton.jsx"
    ]
    
    missing = []
    for comp in required_components:
        path = components_path / comp
        if not path.exists():
            missing.append(comp)
        else:
            print(f"  ✓ {comp}")
    
    if missing:
        print(f"  ✗ Missing components: {missing}")
        return False
    
    return True

def test_api_endpoints():
    """Test API endpoint configuration"""
    frontend_path = Path(__file__).parent.parent / "app" / "frontend"
    app_jsx = frontend_path / "src" / "App.jsx"
    
    print("\nTesting API endpoints...")
    
    try:
        content = app_jsx.read_text(encoding='utf-8')
        
        # Check for localhost:8080 (correct)
        if "localhost:8080" in content:
            print("  ✓ Uses localhost:8080 for API")
        else:
            print("  ⚠ May not be using localhost:8080")
        
        # Check for old remote IP (incorrect)
        if "141.100.238.104" in content:
            print("  ✗ Still contains old remote IP address!")
            return False
        
        # Check for required API endpoints
        endpoints = [
            "/api/analysis/analyze",
            "/api/analysis/risk-map",
            "/api/analysis/professional"
        ]
        
        for endpoint in endpoints:
            if endpoint in content:
                print(f"  ✓ Uses {endpoint}")
            else:
                print(f"  ⚠ May not use {endpoint}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error reading App.jsx: {e}")
        return False

def test_vite_config():
    """Test Vite configuration"""
    frontend_path = Path(__file__).parent.parent / "app" / "frontend"
    vite_config = frontend_path / "vite.config.js"
    
    print("\nTesting vite.config.js...")
    
    try:
        content = vite_config.read_text(encoding='utf-8')
        
        # Check for proxy configuration
        if "proxy" in content and "localhost:8080" in content:
            print("  ✓ Proxy configured for localhost:8080")
        else:
            print("  ⚠ Proxy may not be configured correctly")
        
        # Check for port
        if "port: 3006" in content or "port:3006" in content:
            print("  ✓ Port 3006 configured")
        else:
            print("  ⚠ Port may not be 3006")
        
        return True
    except Exception as e:
        print(f"  ✗ Error reading vite.config.js: {e}")
        return False

def main():
    """Run all frontend tests"""
    print("=" * 60)
    print("FRONTEND VALIDATION TESTS")
    print("=" * 60)
    
    results = []
    
    results.append(("Structure", test_frontend_structure()))
    results.append(("package.json", test_package_json()))
    results.append(("Components", test_components()))
    results.append(("API Endpoints", test_api_endpoints()))
    results.append(("Vite Config", test_vite_config()))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ Frontend structure looks good!")
        return 0
    else:
        print("\n⚠ Some issues found. Review above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
