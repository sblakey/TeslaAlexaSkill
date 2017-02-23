"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function

# --------------- Tesla-specific functionality ---------------------------------

from __future__ import print_function

import urllib2
import json
from urllib import urlencode

import os
TOKEN = os.environ['TOKEN']

class VehicleAPI(object):
    def __init__(self, controller, vehicle_id = None):
        self.__controller = controller
        self.__vehicle_id = vehicle_id or self.first_vehicle_id()

    def first_vehicle_id(self):
        return str(self.vehicles()[0]["id"])
        
    def vehicles(self):
        result = self.json_rest_v1('/vehicles')
        return result

    def json_rest_v1(self, path, data=None):
        url = 'https://owner-api.teslamotors.com/api/1' + path
        print("Requesting", url)
        try:
            request= urllib2.Request(url, data)
            print("Data", data)
            request.add_header('Authorization', 'Bearer ' + TOKEN)
            response = urllib2.urlopen(request)
            return json.load(response)["response"]
        except urllib2.HTTPError as e:
            self.__controller.error(e)
            return {
                'result': False
            }
    
    def command(self, action):
        vehicle = self.__vehicle_id
        return self.json_rest_v1('/vehicles/' + vehicle + '/command/' + action,
            urlencode({"vehicle_id": vehicle}))

    def climate_state(self):
        vehicle = self.__vehicle_id
        return self.json_rest_v1("/vehicles/" + vehicle + "/data_request/climate_state", None)

    def precondition(self):
        return self.command('auto_conditioning_start')

    def wake(self):
        vehicle = self.__vehicle_id
        wake_response = self.json_rest_v1("/vehicles/" + vehicle + "/wake_up", {})
        if not wake_response['result']:
            return wake_response
        return None

    def wake_and_then(self, callback):
        return self.wake() or callback()
            
    def get_climate(self):
        return self.wake_and_then(self.climate_state)
    
    def wake_and_precondition(self):
        return self.wake_and_then(self.precondition)
            
    def stop_precondition(self):
        vehicle = self.__vehicle_id
        return self.command('auto_conditioning_stop')
            
    def vehicle_id(self):
        return self.__vehicle_id

# --------------- Helpers that build all of the responses ----------------------


class SkillController:
    def __init__(self, intent=None, session=None, session_attributes=None):
        self.__intent = intent
        self.__session = session
        self.__session_attributes = session_attributes
        self.__should_end_session = True
        self.__error = None
    
    def get_welcome_response(self):
        """ If we wanted to initialize the session to have some attributes we could
        add those here
        """
        card_title = "Welcome"
        speech_output = "This skill is 100% unofficial " \
                    "You can precondition the HVAC system of your car by saying, " \
                    "warm up"
        # If the user either does not reply to the welcome message or says something
        # that is not understood, they will be prompted again with this text.
        reprompt_text = "I understand the phrases: warm up, cool down, and status"
        self.speechlet(cart_title, speech_output, reprompt_text)
        self.keep_session_open()
        return self.build_response()


    def handle_session_end_request(self):
        card_title = "Session Ended"
        speech_output = "Have a nice day! "
        self.speechlet(card_title, speech_output)
        return self.build_response()

    def climate(self):
        intent = self.__intent
        vehicle_id = self.vehicle_id()
        climate_response = VehicleAPI(vehicle_id).get_climate()
        print("Climate response: " + str(climate_response))
        inside = climate_response.get("inside_temp")
        outside = climate_response.get("outside_temp")
        setting = climate_response.get("driver_temp_setting")
        speech_output = "Your car is currently at " + str(inside) + " degrees, with a setting of " + str(setting) + " degrees."
        self.speechlet(intent['name'], speech_output)
        return self.build_response()

    def precondition(self):
        intent = self.__intent
        vehicle_id = self.vehicle_id()
        result = VehicleAPI(vehicle_id).wake_and_precondition()
        print("auto_conditioning_start response: " + str(result))
        speech_output = "OK, your car is preparing"
        if not result['result']:
            speech_output = "Sorry " + response['reason']
        self.speechlet(intent['name'], speech_output)
        return self.build_response()
        
    def stop_precondition(self):
        intent = self.__intent
        vehicle_id = self.vehicle_id()
        result = VehicleAPI(vehicle_id).tesla_stop_precondition()
        print("auto_conditioning_stop response: " + str(result))
        speech_output = "OK, your car is no longer preparing"
        if not result['result']:
            return "Sorry " + response['reason']
        self.speechlet(intent['name'], speech_output)
        return self.build_response()
            
    def vehicle_id(self):
        return self.__session_attributes.get('vehicle_id') or self.__session.get('attributes', {}).get('vehicle_id')

    def error(self, error):
        self.__error = error
        title = "An error occured accessing the Tesla API"
        output = "Unable to complete action: " + error.reason
        if isinstance(error, urllib2.HTTPError):
            title = "HTTP " + error.code + " accessing Tesla API",
            output = "Unable to use Tesla API: " + error.reason
            if 401 == error.code:
                title = "Authentication Failure"
                output = "Please authenticate using the Alexa app"
        self.speechlet(title, output)
        
    def keep_session_open(self):
        self.__should_end_session = False

    def speechlet(self, title, output, reprompt_text=None):
        self.__title = title
        self.__output = output
        self.__reprompt_text = reprompt_text
    
    def build_response(self):
        return {
            'version': '1.0',
            'sessionAttributes': self.__session_attributes,
            'response': self.build_speechlet_response()
        }

    def build_speechlet_response(self):
        return {
            'outputSpeech': {
                'type': 'PlainText',
                'text': self.__output
            },
            'card': self.build_card(),
            'reprompt': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': self.__reprompt_text
                }
            },
            'shouldEndSession': self.__should_end_session
        }

    def build_card(self):
        if (self.__error and isinstance(self.__error, urllib2.HTTPError) and 401 == self.__error.code):
            return {
                'type': 'LinkAccount'
            }
        else:
            return {
                'type': 'Simple',
                'title': self.__title,
                'content': self.__output
            }


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])
    return {"vehicle_id": VehicleAPI().vehicle_id()}


def on_launch(launch_request, session, session_attributes):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return SkillController(None, session, session_attributes).get_welcome_response()


def on_intent(intent_request, session, session_attributes):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    controller = SkillController(intent, session, session_attributes)

    # Dispatch to your skill's intent handlers
    if intent_name == "Climate":
        return controller.climate()
    elif intent_name == "Precondition":
        return controller.precondition()
    elif intent_name == "AMAZON.HelpIntent":
        return controller.get_welcome_response()
    elif intent_name == "AMAZON.StopIntent":
        return controller.stop_precondition()
    elif intent_name == "AMAZON.CancelIntent":
        return controller.handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")
    session_attributes = {}
    if event['session']['new']:
        session_attributes = on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'], session_attributes)
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'], session_attributes)
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
