from __future__ import print_function
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from voicelabs import VoiceInsights
import configparser


config = configparser.ConfigParser()
config.read('config.txt')

vi_appToken = config['voicelabs']['api_key']
vi = VoiceInsights()


# ---------------------- Helpers That Build the Responses ----------------------

def build_speechlet_response(output, should_end_session):
    """ Return a speech output after an Alexa function is executed.

    Builds a simple speech response after the user invokes a particular Alexa
    function. The response used here is a simple, plain text response but can be
    enhanced by customizing the card that shows to users that have graphical displays
    (like the Echo Show or the Alexa app). See 
    https://developer.amazon.com/docs/custom-skills/include-a-card-in-your-skills-response.html
    for more details about customizing the response.

    You can also specify whether the session should be ended after this response is heard,
    or whether Alexa should prompt for another input from the user using the should_end_session
    parameter.

    Args:
        output: A string that Alexa will read to the user as the output.
        should_end_session: True if the session should end after hearing this response.
                            False if the session should say open for another input from
                                  the user.

    Returns:
        Dictionary containing the output speech and whether or not the session should end.
    """

    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    """ Build the actual response needed by Alexa.

    In addition to the speech output generated by build_speechlet_response(),
    Alexa requires an additional session_attributes dictionary that contains any
    information about the user's current session that needs to be "remembered"
    throughout the session. This function builds that full response.

    Args:
        session_attributes: A dictionary containing any attributes that need to be
                            "remembered" throughout the session.
        speechlet_response: The actual speech that Alexa will say as the output.
                            This is typically generated by the build_speechlet_response()
                            function.

    Returns:
        Dictionary containing the full response (attributes & speech) needed by Alexa.
    """
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

# ------------------------------------------------------------------------------


# --------------------------- General Alexa Responses --------------------------

def get_welcome_response():
    """ Build the Alexa welcome response heard when the user invokes the skill with
        "Alexa, Launch Gronsky's".

    Returns:
        Dictionary containing the welcome response
    """
    session_attributes = {}

    speech_output = (
        "Welcome to the Gronsky's Alexa skill! "
        "To hear some information about Gronsky's, say 'Tell me about Gronsky's.' "
        "To hear Gronsky's pancake of the month, say 'Pancake of the Month'.")

    reprompt_text = (
        "Sorry, I didn't catch that. "
        "Say 'Tell me about Gronsky's' to hear some information about Gronsky's or say 'Pancake of the Month' to hear the pancake of the month."
        )
    
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(speech_output, should_end_session))


def get_help_response():
    """ Build the Alexa help response heard when the user asks for help at any point.

    Returns:
        Dictionary containing the help response
    """
    session_attributes = {}

    speech_output = (
        "Hello! "
        "This skill will tell you information about Gronsky's, a restaurant located in High Bridge, NJ. "
        "To hear some information about Gronsky's, say 'Tell me about Gronsky's.' "
        "To hear Gronsky's pancake of the month, say 'Pancake of the Month'."
        )

    reprompt_text = (
        "Sorry, I didn't catch that. "
        "Say 'Tell me about Gronsky's' to hear some information about Gronsky's or say 'Pancake of the Month' to hear the pancake of the month."
        )
    
    should_end_session = False
    
    return build_response(session_attributes, build_speechlet_response(speech_output, should_end_session))


def handle_session_end_request():
    """ Build the Alexa response heard when the user ends the skill with "Alexa, stop".

    Returns:
        Dictionary containing the response heard when the user ends the skill
    """

    session_attributes = {}

    speech_output = "Thanks for using the Gronsky's Alexa skill! Hope you visit us soon! Goodbye!" 
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(speech_output, should_end_session))

# ------------------------------------------------------------------------------

# -------------------------- Skill-Specific Functions --------------------------

def pancake_of_the_month(intent, session):
    """ Scrape the Gronsky's website for the pancake of the month.

    Uses BeautifulSoup and requests to scrape http://www.gronskys.com, then parses the HTML
    for the current month's pancake.

    To prevent the wrong pancake from being delivered to the user (if the website hasn't yet
    been updated for the current month), an additional check confirms that the month on the
    website matches the actual current month. Otherwise, it delivers a friendly message to
    the user telling them the pancake isn't available yet.

    Args:
        intent: Dictionary containing the intent name ("PancakeOfTheMonth") and other data.
        session: Dictionary containing data related to the current session

    Returns:
        Alexa response with speech indicating the current pancake of the month.

    Todo:
        * Should the skill stop when the pancake of the month is heard, or should Alexa ask
          if the user wants anything else?
    """

    session_attributes = {}
    
    # Visit Gronsky's website and parse the content using BeautifulSoup
    r = requests.get('http://www.gronskys.com/')
    soup = BeautifulSoup(r.content, 'html.parser')

    # Retrieve the current month
    current_month = datetime.now().strftime('%B').upper()
    correct_month = False

    # If the month listed on Gronsky's website is the actual current month, add a flag
    # stating that the website is showing the current month.
    for heading in soup.find_all("h2", { "class" : "av-special-heading-tag " }):
        if current_month in heading.text.upper():
            correct_month = True
    
    # If the website shows the current month, parse the HTML for the pancake of the month
    # and create a string with the pancake of the month. This will be the output spoken
    # to the user.
    if correct_month:
        current_pancake = soup.find("div", { "class" : "av-subheading" }).text.strip()
        speech_output = "The pancake of the month for {month} is {pancake}. ".format(
            month=current_month.capitalize(),
            pancake=current_pancake
        )
    else:
        # If the website does not show the correct month, update the speech output to 
        # tell the user that the information isn't updated yet.
        speech_output = "Sorry, but the pancake of the month isn't available yet! Try again at a later time. "

    speech_output += "To hear more information about Gronsky's, say 'Tell me about Gronsky's'. Otherwise, say 'Stop' to quit."

    # After the pancake of the month is spoken, keep the session open in case they want to hear something else.
    should_end_session = False

    # Return an Alexa response with speech indicating the current pancake of the month.
    return build_response(session_attributes, build_speechlet_response(speech_output, should_end_session))


def about_gronskys(intent, session):
    session_attributes = {}

    speech_output = (
        "Gronsky's Milk House is a family-owned ice cream store and restaurant located at 125 West Main Street in High Bridge, New Jersey. "
        "It was founded in 1978 by Jackie and Steve Gronsky. "
        "Originally a small convenience and ice cream store, Gronsky’s added a restaurant in 1988 to serve breakfast and lunch. "
        )

    speech_output += "To hear Gronsky's pancake of the month, say 'Pancake of the Month'. Otherwise, say 'Stop' to quit."

    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(speech_output, should_end_session))

# ------------------------------------------------------------------------------

    
# -------------------------------- Alexa Intents -------------------------------

def on_intent(intent_request, session):
    """ Decide which function to run based on the intent triggered by the user's input.

    Note: The launch intent (triggered when the user says "Alexa, launch Gronsky's" is
          found in the on_launch() function.)

    Args:
        intent_request: Dictionary containing data about the intent triggered by the user's
                        input.
        session: Dictionary containing data related to the current session

    Returns:
        The function that should run based on the intent triggered by the user's input.
    """

    print("on_intent requestId=" + intent_request['requestId'] + ", sessionId=" + session['sessionId'])
    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    if intent_name == "AMAZON.HelpIntent":
        response = get_help_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        response = handle_session_end_request()
    elif intent_name == "AboutGronskys":
        response = about_gronskys(intent, session)
    elif intent_name == "PancakeOfTheMonth":
        response = pancake_of_the_month(intent, session)
    else:
        raise ValueError("Invalid intent")

    vi.track(intent_name, intent_request, response)

    return response

# ------------------------------------------------------------------------------

# ------------------------------ Generic Events --------------------------------

def on_session_started(session_started_request, session):
    """ Print data about the session when it begins (for logging). """
    print("on_session_started requestId=" + session_started_request['requestId']+ ", sessionId=" + session['sessionId'])
    vi.initialize(appToken, session)

def on_launch(launch_request, session):
    """ Print data about the session when the skill launches (for logging) 
        and launch the welcome response.
    """

    print("on_launch requestId=" + launch_request['requestId'] + ", sessionId=" + session['sessionId'])
    return get_welcome_response()
    
def on_session_ended(session_ended_request, session):
    """ Print data about the session when it ends (for logging). """
    print("on_session_ended requestId=" + session_ended_request['requestId'] + ", sessionId=" + session['sessionId'])

# ------------------------------------------------------------------------------

# ------------------------------- Main Handler ---------------------------------

def lambda_handler(event, context):
    """This required function launches other related functions based on 
    the type of event incurred.
    """

    print("event.session.application.applicationId=" + event['session']['application']['applicationId'])
    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']}, event['session'])
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

# ------------------------------------------------------------------------------