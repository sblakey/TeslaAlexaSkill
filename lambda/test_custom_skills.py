import custom_skill
import unittest
import urllib2

class APIStub(custom_skill.VehicleAPI):
    def __init__(self, error_handler, response):
        super(APIStub, self).__init__(error_handler, "1")
        self.response = response

    def json_rest_v1(self, path, data=None):
        return self.response

class VehicleTestCase(unittest.TestCase):
    def error(self, e):
        self.fail(e)


    def test_first_vehicle_id(self):
        VEHICLES_SUCCESS = [
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
        stub = APIStub(self, VEHICLES_SUCCESS)
        self.assertEqual(stub.first_vehicle_id(), "321")

    def test_command(self):
        COMMAND_SUCCESS = {
            "result": True,
            "reason": ""
        }
        stub = APIStub(self, COMMAND_SUCCESS)
        self.assertTrue(stub.command("auto_conditionin_start")["result"])
        self.assertTrue(stub.precondition()["result"])
        self.assertTrue(stub.stop_precondition()["result"])

    def test_climate_state(self):
        CLIMATE_SUCCESS = {
                "inside_temp": 17.0,
                "outside_temp": 9.5,
                "driver_temp_setting": 22.6,
                "passenger_temp_setting": 22.6,
                "is_auto_conditioning_on": False,
                "is_front_defroster_on": None,
                "is_rear_defroster_on": False,
                "fan_status": 0
        }
        response = APIStub(self, CLIMATE_SUCCESS).climate_state()
        self.assertEqual(response["inside_temp"], 17.0)
        self.assertEqual(response["outside_temp"], 9.5)

    def test_wake(self):
        COMMAND_SUCCESS = {
            "result": True,
            "reason": ""
        }
        response = APIStub(self, COMMAND_SUCCESS).wake()

    def test_wake_and_precondition(self):
        COMMAND_SUCCESS = {
            "result": True,
            "reason": ""
        }
        response = APIStub(self, COMMAND_SUCCESS).wake_and_precondition()
        self.assertTrue(response["result"])
