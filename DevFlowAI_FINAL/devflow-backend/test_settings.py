"""
Test script to verify settings configuration loads correctly
and security validations work as expected.
"""
import os
import sys

def test_settings_load():
    """Test that settings load correctly with .env file"""
    print("Testing settings configuration...")
    
    try:
        from src.config.settings import settings
        
        # Verify critical settings are loaded
        assert settings.SECRET_KEY, "SECRET_KEY is not set"
        assert settings.JWT_SECRET, "JWT_SECRET is not set"
        
        print(f"[OK] SECRET_KEY loaded: {settings.SECRET_KEY[:10]}... (length: {len(settings.SECRET_KEY)})")
        print(f"[OK] JWT_SECRET loaded: {settings.JWT_SECRET[:10]}... (length: {len(settings.JWT_SECRET)})")
        print(f"[OK] DEBUG mode: {settings.DEBUG}")
        print(f"[OK] APP_NAME: {settings.APP_NAME}")
        
        # Test production validation (when DEBUG=False)
        if not settings.DEBUG:
            if len(settings.SECRET_KEY) < 32:
                print("[FAIL] SECRET_KEY is less than 32 characters in production mode")
                return False
            if len(settings.JWT_SECRET) < 32:
                print("[FAIL] JWT_SECRET is less than 32 characters in production mode")
                return False
            print("[OK] Production validation passed")
        else:
            print("[INFO] Running in DEBUG mode - production validations skipped")
        
        print("\n[OK] All settings tests passed!")
        return True
        
    except ValueError as e:
        print(f"[FAIL] {e}")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_missing_secrets():
    """Test that missing secrets raise appropriate errors"""
    print("\n\nTesting missing secrets validation...")
    
    # Save original values
    original_secret = os.environ.get('SECRET_KEY')
    original_jwt = os.environ.get('JWT_SECRET')
    original_debug = os.environ.get('DEBUG')
    
    try:
        # Test with missing SECRET_KEY in production
        os.environ['DEBUG'] = 'false'
        os.environ['SECRET_KEY'] = ''
        
        # Force reload of settings module
        if 'src.config.settings' in sys.modules:
            del sys.modules['src.config.settings']
        
        try:
            from src.config.settings import settings
            print("[FAIL] Should have raised error for missing SECRET_KEY")
            return False
        except ValueError as e:
            print(f"[OK] Correctly raised error for missing SECRET_KEY: {e}")
        
        print("\n[OK] Missing secrets validation test passed!")
        return True
        
    finally:
        # Restore original values
        if original_secret:
            os.environ['SECRET_KEY'] = original_secret
        if original_jwt:
            os.environ['JWT_SECRET'] = original_jwt
        if original_debug:
            os.environ['DEBUG'] = original_debug
        
        # Reload settings with original values
        if 'src.config.settings' in sys.modules:
            del sys.modules['src.config.settings']

if __name__ == "__main__":
    print("=" * 60)
    print("DevFlow AI - Settings Configuration Tests")
    print("=" * 60)
    
    # Test 1: Normal settings load
    test1_passed = test_settings_load()
    
    # Test 2: Missing secrets validation
    test2_passed = test_missing_secrets()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("[SUCCESS] ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("[FAILED] SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)

# Made with Bob
