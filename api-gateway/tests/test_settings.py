"""
Test Suite for API Gateway Settings Configuration
"""
import pytest
from pydantic import ValidationError
from app.config.settings import Settings


class TestSettingsValidation:
    """Test settings validation rules"""

    def test_load_with_defaults(self):
        """Test 1: Load settings with default values"""
        settings = Settings()

        assert settings.jwt_algorithm == "HS256"
        assert settings.gateway_port == 3000
        assert settings.request_timeout == 30
        assert settings.max_retries == 3
        assert settings.environment == "development"
        assert settings.log_level == "INFO"
        assert settings.get_cors_origins_list() == ["*"]
        print("✅ Test 1 PASSED: Defaults loaded correctly")

    def test_invalid_environment(self):
        """Test 2: Invalid environment value raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Settings(environment="invalid_env")

        errors = exc_info.value.errors()
        assert any("environment" in str(error) for error in errors)
        print("✅ Test 2 PASSED: Invalid environment rejected")

    def test_invalid_log_level(self):
        """Test 3: Invalid log level raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Settings(log_level="INVALID")

        errors = exc_info.value.errors()
        assert any("log_level" in str(error) for error in errors)
        print("✅ Test 3 PASSED: Invalid log level rejected")

    def test_negative_timeout(self):
        """Test 4: Negative timeout raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Settings(request_timeout=-10)

        errors = exc_info.value.errors()
        assert any("request_timeout" in str(error) for error in errors)
        print("✅ Test 4 PASSED: Negative timeout rejected")

    def test_timeout_too_large(self):
        """Test 5: Timeout > 300 raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Settings(request_timeout=500)

        errors = exc_info.value.errors()
        assert any("request_timeout" in str(error) for error in errors)
        print("✅ Test 5 PASSED: Timeout > 300 rejected")

    def test_production_short_jwt_secret(self):
        """Test 6: Production with short JWT secret raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                environment="production",
                jwt_secret_key="short_key_12345"  # Only 17 chars, needs 32
            )

        errors = exc_info.value.errors()
        assert any("jwt_secret_key" in str(error) for error in errors)
        print("✅ Test 6 PASSED: Production short JWT secret rejected")

    def test_development_short_jwt_secret(self):
        """Test 7: Development with short JWT secret (< 16) raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                environment="development",
                jwt_secret_key="short"  # Only 5 chars, needs 16
            )

        errors = exc_info.value.errors()
        assert any("jwt_secret_key" in str(error) for error in errors)
        print("✅ Test 7 PASSED: Development short JWT secret rejected")

    def test_development_valid_jwt_secret(self):
        """Test 8: Development with valid JWT secret (>= 16) passes"""
        settings = Settings(
            environment="development",
            jwt_secret_key="1234567890123456"  # Exactly 16 chars
        )

        assert settings.jwt_secret_key == "1234567890123456"
        assert settings.environment == "development"
        print("✅ Test 8 PASSED: Development valid JWT secret accepted")

    def test_production_valid_jwt_secret(self):
        """Test 9: Production with valid JWT secret (>= 32) passes"""
        settings = Settings(
            environment="production",
            jwt_secret_key="12345678901234567890123456789012"  # Exactly 32 chars
        )

        assert settings.environment == "production"
        print("✅ Test 9 PASSED: Production valid JWT secret accepted")

    def test_max_retries_out_of_range(self):
        """Test 10: max_retries > 5 raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Settings(max_retries=10)

        errors = exc_info.value.errors()
        assert any("max_retries" in str(error) for error in errors)
        print("✅ Test 10 PASSED: max_retries > 5 rejected")

    def test_gateway_port_invalid(self):
        """Test 11: gateway_port < 1024 raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Settings(gateway_port=80)

        errors = exc_info.value.errors()
        assert any("gateway_port" in str(error) for error in errors)
        print("✅ Test 11 PASSED: gateway_port < 1024 rejected")

    def test_cors_origins_parsing(self):
        """Test 12: CORS origins parsed from comma-separated string"""
        settings = Settings(
            cors_origins="http://localhost:3000,http://localhost:8080,https://example.com"
        )

        expected = [
            "http://localhost:3000",
            "http://localhost:8080",
            "https://example.com"
        ]
        assert settings.get_cors_origins_list() == expected
        print("✅ Test 12 PASSED: CORS origins parsed correctly")

    def test_cors_origins_wildcard(self):
        """Test 13: CORS origins wildcard"""
        settings = Settings(cors_origins="*")

        assert settings.get_cors_origins_list() == ["*"]
        print("✅ Test 13 PASSED: CORS wildcard handled")

    def test_environment_case_insensitive(self):
        """Test 14: Environment validation is case-insensitive"""
        settings = Settings(environment="PRODUCTION")

        assert settings.environment == "production"  # Normalized to lowercase
        print("✅ Test 14 PASSED: Environment normalized to lowercase")

    def test_log_level_case_insensitive(self):
        """Test 15: Log level validation is case-insensitive"""
        settings = Settings(log_level="debug")

        assert settings.log_level == "DEBUG"  # Normalized to uppercase
        print("✅ Test 15 PASSED: Log level normalized to uppercase")

    def test_helper_methods(self):
        """Test 16: Helper methods work correctly"""
        dev_settings = Settings(environment="development")
        prod_settings = Settings(
            environment="production",
            jwt_secret_key="12345678901234567890123456789012"
        )

        assert dev_settings.is_development() is True
        assert dev_settings.is_production() is False
        assert prod_settings.is_production() is True
        assert prod_settings.is_development() is False
        print("✅ Test 16 PASSED: Helper methods work correctly")


def run_all_tests():
    """Run all tests manually"""
    print("\n🧪 Running API Gateway Settings Tests...\n")

    test = TestSettingsValidation()

    # Run each test
    test.test_load_with_defaults()
    test.test_invalid_environment()
    test.test_invalid_log_level()
    test.test_negative_timeout()
    test.test_timeout_too_large()
    test.test_production_short_jwt_secret()
    test.test_development_short_jwt_secret()
    test.test_development_valid_jwt_secret()
    test.test_production_valid_jwt_secret()
    test.test_max_retries_out_of_range()
    test.test_gateway_port_invalid()
    test.test_cors_origins_parsing()
    test.test_cors_origins_wildcard()
    test.test_environment_case_insensitive()
    test.test_log_level_case_insensitive()
    test.test_helper_methods()

    print("\n✅ ALL TESTS PASSED! 🎉\n")


if __name__ == "__main__":
    run_all_tests()
