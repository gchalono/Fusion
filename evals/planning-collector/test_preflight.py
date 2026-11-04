import unittest
from preflight import inspect, missing_authorization
from test_gateway import config


class PreflightTests(unittest.TestCase):
    def test_missing_config_never_runs(self):
        result = inspect({})
        self.assertEqual(result["status"], "PILOT_BLOCKED")
        self.assertEqual(result["model_calls"], 0)
        self.assertIn("paid_inference_authorization", result["missing_authorization"])

    def test_complete_declaration_still_requires_engineering_proof(self):
        c = config(credential_env_var="OFFLINE_TEST_CREDENTIAL", pilot_goal="offline preflight check",
                   answerer="scripted", max_interview_turns=1, live_authorized=True)
        self.assertEqual(missing_authorization(c), [])
        result = inspect(c)
        self.assertEqual(result["status"], "PILOT_BLOCKED")
        self.assertTrue(result["remaining_engineering"])
        self.assertEqual(result["model_calls"], 0)


if __name__ == "__main__":
    unittest.main()
