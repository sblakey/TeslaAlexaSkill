import custom_skill
import unittest
import urllib2

class VehicleAPIVehiclesSuccessTestCase(unittest.TestCase):
    STUB_RESPONSE = [
                {
                    "color": None,
                    "display_name": None,
                    "id": 321,
                    "option_codes": "",
                    "user_id": 123,
                    "vehicle_id": 1234567890,
                    "vin": "5YJSA1CN5CFP01657",
                    "tokens": [
                        "x",
                        "x"
                        ],
                    "state": "online"
                }
            ]

    def error(self, e):
        self.fail(e)

    def setUp(self):
        self.vapi = custom_skill.VehicleAPI(self, "1")
        self.vapi.json_rest_v1 = self.json_rest_v1

    def json_rest_v1(self, path, data=None):
        return VehicleAPIVehiclesSuccessTestCase.STUB_RESPONSE

    def test_first_vehicle_id(self):
        self.assertEqual(self.vapi.first_vehicle_id(), "321")


class VehicleAPICommandSuccessTestCase(unittest.TestCase):
    STUB_RESPONSE = {
            "result": True,
            "reason": ""
        }

    def error(self, e):
        self.fail(e)

    def setUp(self):
        self.vapi = custom_skill.VehicleAPI(self, "1")
        self.vapi.json_rest_v1 = self.json_rest_v1

    def json_rest_v1(self, path, data=None):
        return VehicleAPICommandSuccessTestCase.STUB_RESPONSE

    def test_command(self):
        response = self.vapi.command("auto_conditioning_start")
        print "Response is " + str(response)
        self.assertTrue(response["result"])

