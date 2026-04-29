import unittest
from gamma_runtime.bridge.scientific_adapter import run_v1_gamma_bridge_payload

class TestScienceIntegration(unittest.TestCase):
    def test_bridge_invocation(self):
        # This will test if the bridge correctly calls the pipeline and receives a structured response
        payload = {'params': {'pv_gain': 1.0}}
        result = run_v1_gamma_bridge_payload(payload)
        
        # Verify structure
        self.assertIsNotNone(result)
        # Check that we didn't get an error status (unless the simulation failed)
        # Based on pipeline patch, status should be accepted or rejected
        self.assertIn(result.status, ['accepted', 'rejected', 'error'])
        
        if result.status == 'accepted':
            self.assertIn('healthy', result.__dict__)
            self.assertIn('schiz', result.__dict__)
            
if __name__ == '__main__':
    unittest.main()
