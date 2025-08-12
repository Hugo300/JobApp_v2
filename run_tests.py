#!/usr/bin/env python3
"""
Test runner script for the Job Application Manager
"""
import sys
import subprocess
import os

def run_tests():
    """Run all tests with coverage reporting"""
    print("🧪 Running Job Application Manager Tests...")
    print("=" * 50)
    
    # Check if pytest is available
    try:
        import pytest
        import pytest_flask
        import pytest_cov
    except ImportError as e:
        print(f"❌ Missing test dependencies: {e}")
        print("Please install test dependencies:")
        print("pip install pytest pytest-flask pytest-cov coverage")
        return 1
    
    # Set environment for testing
    os.environ['FLASK_ENV'] = 'testing'
    
    # Run tests with coverage
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '--verbose',
        '--tb=short',
        '--cov=.',
        '--cov-report=html',
        '--cov-report=term-missing',
        '--cov-config=.coveragerc'
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            print("\n🎉 All tests passed!")
            print("📊 Coverage report generated in htmlcov/index.html")
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
        
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

def run_specific_test(test_path):
    """Run a specific test file or test function"""
    print(f"🧪 Running specific test: {test_path}")
    print("=" * 50)
    
    os.environ['FLASK_ENV'] = 'testing'
    
    cmd = [
        sys.executable, '-m', 'pytest',
        test_path,
        '--verbose',
        '--tb=short'
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return 1

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run specific test
        test_path = sys.argv[1]
        exit_code = run_specific_test(test_path)
    else:
        # Run all tests
        exit_code = run_tests()
    
    sys.exit(exit_code)
