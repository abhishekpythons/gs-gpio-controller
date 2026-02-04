#!/usr/bin/env python3
"""
GPIO Controller Test Suite
Tests backend API functionality and database setup
"""

import requests
import json
import time
import sys

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'

class GPIOControllerTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.test_results = []
        
    def print_header(self, text):
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}{text:^60}{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
        
    def print_test(self, name, passed, message=""):
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"{status} - {name}")
        if message:
            print(f"     {Colors.YELLOW}{message}{Colors.END}")
        self.test_results.append((name, passed))
        
    def test_server_connection(self):
        """Test if server is running"""
        self.print_header("Testing Server Connection")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_test("Server is running", True, f"Status: {data.get('status')}")
                return True
            else:
                self.print_test("Server is running", False, f"Status code: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.print_test("Server is running", False, "Cannot connect to server")
            return False
        except Exception as e:
            self.print_test("Server is running", False, str(e))
            return False
            
    def test_register(self):
        """Test user registration"""
        self.print_header("Testing User Registration")
        
        test_user = {
            "username": f"testuser_{int(time.time())}",
            "password": "testpass123",
            "email": "test@example.com"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/register",
                json=test_user,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test_token = data.get('access_token')
                self.print_test("User registration", True, f"Token received")
                return True
            else:
                self.print_test("User registration", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("User registration", False, str(e))
            return False
            
    def test_login(self):
        """Test user login"""
        self.print_header("Testing User Login")
        
        credentials = {
            "username": "admin",
            "password": "admin123"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/login",
                json=credentials,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.print_test("User login", True, "Admin login successful")
                return True
            else:
                self.print_test("User login", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("User login", False, str(e))
            return False
            
    def test_get_user_info(self):
        """Test getting current user info"""
        self.print_header("Testing User Info Retrieval")
        
        if not self.token:
            self.print_test("Get user info", False, "No authentication token")
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/api/user/me",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_test("Get user info", True, f"User: {data.get('username')}")
                return True
            else:
                self.print_test("Get user info", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Get user info", False, str(e))
            return False
            
    def test_get_gpio_pins(self):
        """Test getting GPIO pins"""
        self.print_header("Testing GPIO Pin Retrieval")
        
        if not self.token:
            self.print_test("Get GPIO pins", False, "No authentication token")
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/api/gpio/pins",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                pins = data.get('pins', [])
                self.print_test("Get GPIO pins", True, f"Found {len(pins)} pins")
                
                # Print pin states
                for pin in pins[:4]:  # Show first 4 pins
                    state = "ON" if pin['state'] == 1 else "OFF"
                    print(f"     Pin {pin['pin']}: {state}")
                    
                return True
            else:
                self.print_test("Get GPIO pins", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Get GPIO pins", False, str(e))
            return False
            
    def test_gpio_control(self):
        """Test GPIO pin control"""
        self.print_header("Testing GPIO Pin Control")
        
        if not self.token:
            self.print_test("GPIO control", False, "No authentication token")
            return False
            
        test_pin = 35  # Intel NuC PC
        
        try:
            # Turn pin ON
            response = requests.post(
                f"{self.base_url}/api/gpio/control",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"pin": test_pin, "state": 1},
                timeout=5
            )
            
            if response.status_code == 200:
                self.print_test("GPIO control (ON)", True, f"Pin {test_pin} (Intel NuC PC) turned ON")
                
                # Turn pin OFF
                response = requests.post(
                    f"{self.base_url}/api/gpio/control",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={"pin": test_pin, "state": 0},
                    timeout=5
                )
                
                if response.status_code == 200:
                    self.print_test("GPIO control (OFF)", True, f"Pin {test_pin} (Intel NuC PC) turned OFF")
                    return True
                else:
                    self.print_test("GPIO control (OFF)", False, f"Status: {response.status_code}")
                    return False
            else:
                self.print_test("GPIO control (ON)", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("GPIO control", False, str(e))
            return False
            
    def test_get_logs(self):
        """Test getting activity logs"""
        self.print_header("Testing Activity Log Retrieval")
        
        if not self.token:
            self.print_test("Get activity logs", False, "No authentication token")
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/api/logs?limit=10",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                logs = data.get('logs', [])
                self.print_test("Get activity logs", True, f"Retrieved {len(logs)} log entries")
                
                # Show latest log
                if logs:
                    latest = logs[0]
                    print(f"     Latest: {latest['username']} - {latest['action']}")
                    
                return True
            else:
                self.print_test("Get activity logs", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Get activity logs", False, str(e))
            return False
            
    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        self.print_header("Testing Security - Invalid Credentials")
        
        credentials = {
            "username": "wronguser",
            "password": "wrongpass"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/login",
                json=credentials,
                timeout=5
            )
            
            if response.status_code == 401:
                self.print_test("Invalid credentials rejected", True, "Security check passed")
                return True
            else:
                self.print_test("Invalid credentials rejected", False, "Should return 401")
                return False
        except Exception as e:
            self.print_test("Invalid credentials rejected", False, str(e))
            return False
            
    def test_unauthorized_access(self):
        """Test accessing protected endpoint without token"""
        self.print_header("Testing Security - Unauthorized Access")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/gpio/pins",
                timeout=5
            )
            
            if response.status_code == 403:
                self.print_test("Unauthorized access blocked", True, "Security check passed")
                return True
            else:
                self.print_test("Unauthorized access blocked", False, f"Should return 403, got {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Unauthorized access blocked", False, str(e))
            return False
            
    def print_summary(self):
        """Print test summary"""
        self.print_header("Test Summary")
        
        total = len(self.test_results)
        passed = sum(1 for _, result in self.test_results if result)
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed}{Colors.END}")
        
        if failed == 0:
            print(f"\n{Colors.GREEN}🎉 All tests passed! Your GPIO Controller is working perfectly!{Colors.END}\n")
            return True
        else:
            print(f"\n{Colors.YELLOW}⚠️  Some tests failed. Please check the errors above.{Colors.END}\n")
            return False
            
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{Colors.BLUE}{'='*60}")
        print(f"{'GPIO CONTROLLER TEST SUITE':^60}")
        print(f"{'='*60}{Colors.END}\n")
        
        # Basic connectivity
        if not self.test_server_connection():
            print(f"\n{Colors.RED}Cannot connect to server. Is it running?{Colors.END}")
            print(f"{Colors.YELLOW}Start the server with: ./start.sh{Colors.END}\n")
            return False
            
        # Authentication tests
        self.test_login()
        self.test_register()
        self.test_get_user_info()
        
        # GPIO tests
        self.test_get_gpio_pins()
        self.test_gpio_control()
        
        # Logging tests
        self.test_get_logs()
        
        # Security tests
        self.test_invalid_credentials()
        self.test_unauthorized_access()
        
        # Summary
        return self.print_summary()

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test GPIO Controller API')
    parser.add_argument('--url', default='http://localhost:8000', 
                       help='Base URL of the API (default: http://localhost:8000)')
    
    args = parser.parse_args()
    
    tester = GPIOControllerTester(args.url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
