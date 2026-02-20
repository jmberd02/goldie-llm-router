# Sample complex function to use in the demo
SAMPLE_COMPLEX_FUNCTION = '''
def process_payment(user_id: str, amount: float, currency: str, retry_count: int = 0) -> dict:
    """Process a payment with retry logic and currency conversion."""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    if retry_count > 3:
        raise RuntimeError("Max retries exceeded")
    # ... implementation
'''


def generate_unit_tests(params: dict) -> str:
    """Generate unit tests for a given function."""
    function_code = params.get("function_code", SAMPLE_COMPLEX_FUNCTION)
    language = params.get("language", "python")
    
    # Extract function name from code (simple regex)
    import re
    match = re.search(r'def\s+(\w+)\s*\(', function_code)
    func_name = match.group(1) if match else "target_function"
    
    # Generate realistic pytest test file
    return f'''import pytest
from unittest.mock import Mock, patch
from your_module import {func_name}


class Test{func_name.title().replace("_", "")}:
    """Comprehensive test suite for {func_name}."""
    
    def test_{func_name}_happy_path(self):
        """Test successful execution with valid inputs."""
        result = {func_name}("user_123", 100.0, "USD")
        
        assert result is not None
        assert isinstance(result, dict)
        assert result.get("status") == "success"
    
    def test_{func_name}_with_zero_amount(self):
        """Test that zero amount raises ValueError."""
        with pytest.raises(ValueError, match="Amount must be positive"):
            {func_name}("user_123", 0.0, "USD")
    
    def test_{func_name}_with_negative_amount(self):
        """Test that negative amount raises ValueError."""
        with pytest.raises(ValueError, match="Amount must be positive"):
            {func_name}("user_123", -50.0, "USD")
    
    def test_{func_name}_max_retries_exceeded(self):
        """Test that exceeding max retries raises RuntimeError."""
        with pytest.raises(RuntimeError, match="Max retries exceeded"):
            {func_name}("user_123", 100.0, "USD", retry_count=4)
    
    def test_{func_name}_with_empty_user_id(self):
        """Test behavior with empty user ID."""
        # Assuming empty user_id should be handled gracefully or raise error
        with pytest.raises(ValueError):
            {func_name}("", 100.0, "USD")
    
    def test_{func_name}_with_different_currencies(self):
        """Test currency conversion logic."""
        result_usd = {func_name}("user_123", 100.0, "USD")
        result_eur = {func_name}("user_123", 100.0, "EUR")
        
        assert result_usd["currency"] == "USD"
        assert result_eur["currency"] == "EUR"
    
    @patch('your_module.payment_gateway')
    def test_{func_name}_with_mocked_gateway(self, mock_gateway):
        """Test with mocked external payment gateway."""
        mock_gateway.process.return_value = {{"status": "success", "transaction_id": "txn_123"}}
        
        result = {func_name}("user_123", 100.0, "USD")
        
        mock_gateway.process.assert_called_once()
        assert result["transaction_id"] == "txn_123"
    
    def test_{func_name}_retry_logic(self):
        """Test retry mechanism with incremental retry_count."""
        # First attempt
        result_0 = {func_name}("user_123", 100.0, "USD", retry_count=0)
        assert result_0 is not None
        
        # Second attempt
        result_1 = {func_name}("user_123", 100.0, "USD", retry_count=1)
        assert result_1 is not None
        
        # Third attempt (at limit)
        result_3 = {func_name}("user_123", 100.0, "USD", retry_count=3)
        assert result_3 is not None


@pytest.fixture
def sample_user():
    """Fixture providing a sample user for testing."""
    return {{"user_id": "user_123", "balance": 1000.0}}


def test_{func_name}_integration_with_user_fixture(sample_user):
    """Integration test using user fixture."""
    result = {func_name}(sample_user["user_id"], 50.0, "USD")
    assert result["status"] == "success"
'''
