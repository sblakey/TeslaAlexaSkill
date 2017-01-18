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

class VehicleAPI:
    def __init__(self, vehicle_id = None):
        self.__vehicle_id = vehicle_id or self.tesla_vehicle_id()
        
    def tesla_vehicle_id(self):
        result = self.json_rest_v1('/vehicles')
        print("Vehicle list", result)
        return str(result["response"][0]["id"])
    

    def json_rest_v1(self, path, data=None):
        url = 'https://owner-api.teslamotors.com/api/1' + path
        print("Requesting", url)
        request= urllib2.Request(url, data)
        print("Data", data)
        request.add_header('Authorization', 'Bearer ' + TOKEN)
        response = urllib2.urlopen(request)
        return json.load(response)
    
    def tesla_command(self, action):
        vehicle = self.__vehicle_id
        return self.json_rest_v1('/vehicles/' + vehicle + '/command/' + action,
            urlencode({"vehicle_id": vehicle}))
            
    def tesla_get_climate(self):
        vehicle = self.__vehicle_id
        print("Waking")
        wake_response = self.json_rest_v1("/vehicles/" + vehicle + "/wake_up", {})
        print("Wake response: " + str(wake_response))
        print("Getting climate")
        climate_response = self.json_rest_v1("/vehicles/" + vehicle + "/data_request/climate_state", None)
        print("Climate response: " + str(climate_response))
        inside = climate_response["response"]["inside_temp"]
        outside = climate_response["response"]["outside_temp"]
        setting = climate_response["response"]["driver_temp_setting"]
        return "Your car is currently at " + str(inside) + " degrees, with a setting of " + str(setting) + " degrees."
    
    def tesla_wake_and_precondition(self):
        vehicle = self.__vehicle_id
        print("Waking")
        wake_response = self.json_rest_v1("/vehicles/" + vehicle + "/wake_up", {})
        print("Wake response: " + str(wake_response))
        print("Starting HVAC")
        result = self.tesla_command('auto_conditioning_start')
        print("auto_conditioning_start response: " + str(result))
        if result['response']['result']:
            return "OK, your car is preparing"
        else:
            return "Sorry " + response['reason']
            
    def tesla_stop_precondition(self):
        vehicle = self.__vehicle_id
        print("Stopping HVAC")
        result = self.tesla_command('auto_conditioning_stop')
        print("auto_conditioning_stop response: " + str(result))
        if result['response']['result']:
            return "OK, your car is no longer preparing"
        else:
            return "Sorry " + response['reason']
            
    def vehicle_id(self):
        return self.__vehicle_id

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text=None, should_end_session=True):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }




# --------------- Functions that control the skill's behavior ------------------

def set_color_in_session(intent, session):
    """ Sets the color in the session and prepares the speech to reply to the
    user.
    """

    card_title = intent['name']
    session_attributes = {}
    should_end_session = False

    if 'Color' in intent['slots']:
        favorite_color = intent['slots']['Color']['value']
        session_attributes = create_favorite_color_attributes(favorite_color)
        speech_output = "I now know your favorite color is " + \
                        favorite_color + \
                        ". You can ask me your favorite color by saying, " \
                        "what's my favorite color?"
        reprompt_text = "You can ask me your favorite color by saying, " \
                        "what's my favorite color?"
    else:
        speech_output = "I'm not sure what your favorite color is. " \
                        "Please try again."
        reprompt_text = "I'm not sure what your favorite color is. " \
                        "You can tell me your favorite color by saying, " \
                        "my favorite color is red."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_color_from_session(intent, session):
    session_attributes = {}
    reprompt_text = None

    if session.get('attributes', {}) and "favoriteColor" in session.get('attributes', {}):
        favorite_color = session['attributes']['favoriteColor']
        speech_output = "Your favorite color is " + favorite_color + \
                        ". Goodbye."
        should_end_session = True
    else:
        speech_output = "I'm not sure what your favorite color is. " \
                        "You can say, my favorite color is red."
        should_end_session = False

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

class SkillController:
    def __init__(self, intent=None, session=None, session_attributes=None):
        self.__intent = intent
        self.__session = session
        self.__session_attributes = session_attributes
    
    def get_welcome_response(self):
        """ If we wanted to initialize the session to have some attributes we could
        add those here
        """
        card_title = "Welcome"
        speech_output = "This skill is 100% unofficial " \
                    "You can precondition the HVAC system of your car by saing, " \
                    "warm up"
        # If the user either does not reply to the welcome message or says something
        # that is not understood, they will be prompted again with this text.
        reprompt_text = "I'm not feeling very patient, right now."
        should_end_session = False
        return self.build_response(build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))


    def handle_session_end_request(self):
        card_title = "Session Ended"
        speech_output = "Have a nice day! "
        return self.build_response(build_speechlet_response(
            card_title, speech_output))

    def climate(self):
        intent = self.__intent
        vehicle_id = self.vehicle_id()
        speech_output = VehicleAPI(vehicle_id).tesla_get_climate()
        return self.build_response(build_speechlet_response(
            intent['name'], speech_output))

    def precondition(self):
        intent = self.__intent
        vehicle_id = self.vehicle_id()
        speech_output = VehicleAPI(vehicle_id).tesla_wake_and_precondition()
        return self.build_response(build_speechlet_response(
            intent['name'], speech_output))
        
    def stop_precondition(self):
        intent = self.__intent
        vehicle_id = self.vehicle_id()
        speech_output = VehicleAPI(vehicle_id).tesla_stop_precondition()
        return self.build_response(build_speechlet_response(
            intent['name'], speech_output))
            
    def vehicle_id(self):
        return self.__session_attributes.get('vehicle_id') or self.__session.get('attributes', {}).get('vehicle_id')
        
    
    def build_response(self, speechlet_response):
        return {
            'version': '1.0',
            'sessionAttributes': self.__session_attributes,
            'response': speechlet_response
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
