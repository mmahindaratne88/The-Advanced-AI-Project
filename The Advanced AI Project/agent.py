import os
import pyttsx3
import speech_recognition as sr
import string
from datetime import datetime
import pytz
import wikipedia
import warnings
import requests
import platform
import psutil
import wmi
import configparser
import webbrowser

# Initialize the text-to-speech engine.
engine = pyttsx3.init()

# Set the voice to Microsoft Zira
voices = engine.getProperty('voices')
for voice in voices:
    if "zira" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break

# Function for speech.
def speak(text):
    for word in text.split():
        print(word, end=' ', flush=True)  
    print()  
    engine.say(text)
    engine.runAndWait()

# Function to listen.
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for commands...")
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio).lower()
    except sr.UnknownValueError:
        speak("Command not recognized!")
        return ""

# Function for introductory greeting.
def get_greeting(time):
    hour = time.hour
    parts_of_day = "morning" if 0 <= hour < 12 else "afternoon" if 12 <= hour < 18 else "evening"
    formatted_date_time = get_formatted_date_time().replace("AM", "am").replace("PM", "pm")
    weather_info = get_weather_for_colombo().replace(" Kelvin", " degrees Celsius")
    return f"Good {parts_of_day}! Welcome to the Ghost Protocol! The current date and time in Colombo Sri Lanka is {formatted_date_time}. {weather_info}"

# Function to read values from the config.ini file
def read_config(config_file='config.ini', section='', key=''):
    # Here ConfigParser is a class within the configparser module.
    config = configparser.ConfigParser()
    config.read(config_file)
    try:
        return config.get(section, key)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return None

# Function to get the current date, and time in Colombo, Sri Lanka.
def get_colombo_time():
    colombo_timezone = pytz.timezone('Asia/Colombo')
    return datetime.now(colombo_timezone)

# Function to format date, and time.
def get_formatted_date_time():
    now = get_colombo_time()
    # Determine the suffix for the day of the month
    suffix = 'th' if 11 <= now.day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(now.day % 10, 'th')
    # Format the date and time string with the appropriate suffix
    date_time_str = now.strftime(f'%A, the {now.day}{suffix} of %B, %Y, %I:%M%p')
    # Remove leading zero from the hour if present
    date_time_str = date_time_str.replace(" 0", " ")
    return date_time_str

# Function to remove punctuation from user input.
def remove_punctuation(input_string):
    return input_string.translate(str.maketrans('', '', string.punctuation))

# Function for weather update
def get_weather_for_colombo():
    api_key = read_config(section='WeatherAPI', key='APIKey')
    if api_key is None:
        return "Weather API key not found in configuration."
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    city_name = "Colombo"
    complete_url = f"{base_url}?q={city_name}&appid={api_key}&units=metric"
    response = requests.get(complete_url)
    weather_data = response.json()
    if response.status_code == 200:
        temperature = weather_data['main']['temp']
        pressure = weather_data['main']['pressure']
        humidity = weather_data['main']['humidity']
        weather_description = weather_data['weather'][0]['description']
        return f"The temperature is {temperature} degrees Celsius, the pressure is {pressure}hPa, and the humidity is {humidity}% with {weather_description}."
    else:
        return f"Error {response.status_code}: Unable to get weather data."

# System information
def get_system_information():
    c = wmi.WMI()
    my_system = c.Win32_ComputerSystem()[0]

    # Retrieve processor information
    processor_info = c.Win32_Processor()[0].Name.strip()
    # OS and Python version
    os_version = platform.platform().replace('-', ' ')
    python_version = platform.python_version()

    # RAM details
    ram = psutil.virtual_memory().total / (1024 ** 3)
    # Storage details
    partitions = psutil.disk_partitions()
    storage_details = [psutil.disk_usage(p.device).total / (1024 ** 3) for p in partitions if 'fixed' in p.opts]
    return (f"I am running on a {my_system.Manufacturer} {my_system.Model} Laptop. The Processor is an {processor_info}. "
            f"Available RAM is {ram:.2f} GB. Storage details: {', '.join([f'{sd:.2f} GB' for sd in storage_details])}. "
            f"The Operating System is {os_version}, and the Python version is {python_version}.")

# Function to look up Wikipedia.
def lookup_wikipedia(topic):
    try:
        summary = wikipedia.summary(topic, sentences=3)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Multiple results found for {topic}. Select options: {e.options[:5]}"
    except wikipedia.exceptions.PageError:
        return f"No content found for {topic}."
    except Exception as e:
        return "An error occurred while trying to fetch information from Wikipedia."

warnings.filterwarnings("ignore", category=UserWarning, module='wikipedia')

# Function to get top news headlines for a given country.
def get_news_headlines(country='us'):
    api_key = read_config(section='NewsAPI', key='APIKey')
    if api_key is None:
        return "News API key not found in configuration."

    base_url = f"https://newsapi.org/v2/top-headlines?country={country}&apiKey={api_key}"

    response = requests.get(base_url)
    if response.status_code == 200:
        articles = response.json()['articles']
        headlines = [article['title'] for article in articles]
        return '\n'.join([f"Headline {idx + 1}: {headline}" for idx, headline in enumerate(headlines)])
    else:
        return f"Error {response.status_code}: Unable to fetch news headlines."

# Web search.
def search_query(query):
    webbrowser.open(f"https://www.google.com/search?q={query}")

# Function to process user inputs.
def process_command(command):
    command_clean = remove_punctuation(command.lower())
    if command_clean.startswith('current date and time'):
        speak("The current date and time in Colombo Sri Lanka is " + get_formatted_date_time())
    elif command_clean.startswith('current weather update'):
        weather_info = get_weather_for_colombo()
        speak(weather_info) 
    elif 'system information' in command_clean:
        system_information = get_system_information()
        speak(system_information)
    elif 'look up ' in command_clean:
        topic = command_clean[8:]
        info = lookup_wikipedia(topic)
        speak(info)
    elif 'news headlines' in command_clean:
        speak("Fetching top news headlines...")
        headlines = get_news_headlines()
        headlines = headlines.split('\n')  
        for headline in headlines:
            print(headline)
    elif command_clean.startswith('search'):
         query = command_clean[len('search '):]
         search_query(query)
         speak("Opening Web Browser...")
    elif 'access main server' in command_clean:
         webbrowser.open(f"http://127.0.0.1:5000")
         speak("Accessing Main Server...")
    elif 'exit protocol' in command_clean:
         speak("Terminating Session...")
         return 'exit'
    else:
        speak("Command not recognized!")
    return None  

# The main loop for the AI to run
def main():
    greeting = get_greeting(get_colombo_time())
    speak(greeting)

    use_audio = None
    while use_audio is None:
        choice = input("Select Command Type: ").lower()
        if choice == 'speech':
            use_audio = True
        elif choice == 'text':
            use_audio = False
        else:
            speak("Please choose either 'speech' or 'text'.")

    while True:
        if use_audio:
            command = listen()
        else:
            command = input("Please type a command: ").lower()
            command = remove_punctuation(command)
 
        if command:
            result = process_command(command)
            if result == 'exit':
                break

if __name__ == "__main__":
    main()
