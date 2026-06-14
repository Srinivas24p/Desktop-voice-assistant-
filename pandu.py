from flask import Flask, request, jsonify, render_template_string
import speech_recognition as sr
import pyttsx3
import pywhatkit
import datetime
import wikipedia
import pyjokes
import os
import webbrowser
import requests
import psutil
import platform
import json
import re
from collections import deque
import random

app = Flask(__name__)

WEATHER_API_KEY = "ec6bcd8d48c5b1efcc2bdce6ab2ccae1"  # Replace with your OpenWeatherMap API key
NEWS_API_KEY = "010f34a6a4b742c68d222c210c68c207"     # Replace with your NewsAPI key

conversation_history = deque(maxlen=10)

engine = pyttsx3.init()
engine.setProperty('rate', 170)
voices = engine.getProperty('voices')
if voices:
    engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)

def talk(text, emotion="neutral"):
    print(f"🎙 PANDU ({emotion}):", text)
    if emotion == "excited":
        engine.setProperty('rate', 200)
        engine.setProperty('volume', 1.0)
    elif emotion == "calm":
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.8)
    else:
        engine.setProperty('rate', 170)
        engine.setProperty('volume', 0.9)
    engine.say(text)
    engine.runAndWait()

def get_ai_response(user_input):
    user_input = user_input.lower()
    current_hour = datetime.datetime.now().hour
    if current_hour < 12:
        greeting = "Good morning!"
    elif current_hour < 17:
        greeting = "Good afternoon!"
    else:
        greeting = "Good evening!"
    responses = {
        "how are you": f"{greeting} I'm doing fantastic! Ready to help you with anything you need.",
        "what's your name": "I'm PANDU, your advanced AI voice assistant.",
        "thank you": "You're welcome! I'm always here to help.",
        "hello": f"{greeting} How can I assist you today?",
        "hi": f"Hi there! {greeting.lower()} What would you like me to help you with?",
        "good morning": "Good morning! I hope you have a wonderful day!",
        "good afternoon": "Good afternoon! How has your day been?",
        "good evening": "Good evening! How can I help you unwind?",
        "what can you do": "I can help with weather, news, system info, jokes, music, and more!",
        "who made you": "I was created as your helpful AI assistant.",
        "what time is it": f"It's currently {datetime.datetime.now().strftime('%I:%M %p')}",
        "what day is it": f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}",
        "how old are you": "I'm a digital assistant, so I don't age.",
        "where are you from": "I exist in the digital realm, but I'm here to help you wherever you are!",
        "what's the weather": "Try asking 'weather in [city name]' for specific locations.",
        "tell me news": "Try 'tech news', 'sports news', or just 'news' for general headlines.",
        "are you real": "I'm as real as any AI can be! I'm here and ready to help.",
        "can you learn": "I learn from our conversations to provide better responses.",
    }
    for key, response in responses.items():
        if key in user_input:
            return response
    if "help" in user_input:
        return "I'm here to help! Try asking about weather, news, system info, jokes, music, or anything else."
    return "That's interesting! Try asking me about weather, news, system info, or any other questions!"

def get_weather(city="auto"):
    if WEATHER_API_KEY == "your-openweathermap-api-key-here":
        return get_weather_demo(city)
    try:
        if city == "auto":
            city = "nuzvid"
        city = city.replace("weather in ", "").replace("weather for ", "").replace("weather", "").strip()
        if not city:
            city = "nuzvid"
        weather_url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        }
        response = requests.get(weather_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            temp = round(data['main']['temp'], 1)
            feels_like = round(data['main']['feels_like'], 1)
            humidity = data['main']['humidity']
            pressure = data['main']['pressure']
            description = data['weather'][0]['description'].title()
            city_name = data['name']
            country = data['sys']['country']
            wind_speed = data.get('wind', {}).get('speed', 0)
            weather_info = f"""🌤️ Current Weather in {city_name}, {country}:
📊 Condition: {description}
🌡️ Temperature: {temp}°C (feels like {feels_like}°C)
💧 Humidity: {humidity}%
🌬️ Wind Speed: {wind_speed} m/s
📏 Pressure: {pressure} hPa
🕐 Updated: {datetime.datetime.now().strftime('%I:%M %p')}
📡 Source: OpenWeatherMap"""
            return weather_info
        else:
            return get_weather_demo(city)
    except Exception as e:
        return get_weather_demo(city)

def get_weather_demo(city="Your Location"):
    weather_conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Clear", "Overcast"]
    temp = random.randint(18, 28)
    feels_like = temp + random.randint(-2, 4)
    humidity = random.randint(45, 75)
    wind_speed = round(random.uniform(3.0, 12.0), 1)
    condition = random.choice(weather_conditions)
    return f"""🌤️ Demo Weather for {city}:
📊 Condition: {condition}
🌡️ Temperature: {temp}°C (feels like {feels_like}°C)
💧 Humidity: {humidity}%
🌬️ Wind Speed: {wind_speed} m/s
⚠️ This is demo data for testing."""

def get_latest_news(category="general"):
    try:
        if not NEWS_API_KEY or NEWS_API_KEY == "your api key":
            return "❌ News API key not configured."
        valid_categories = {
            "general": "general",
            "business": "business", 
            "entertainment": "entertainment",
            "health": "health",
            "science": "science",
            "sports": "sports",
            "technology": "technology",
            "tech": "technology",
            "sport": "sports",
            "finance": "business",
            "politics": "general",
            "world": "general"
        }
        category = valid_categories.get(category.lower(), "general")
        news_url = f"https://newsapi.org/v2/top-headlines"
        params = {
            'apiKey': NEWS_API_KEY,
            'category': category,
            'language': 'en',
            'pageSize': 4,
            'sortBy': 'publishedAt'
        }
        response = requests.get(news_url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok' and data.get('articles'):
                articles = data['articles']
                news_items = []
                for i, article in enumerate(articles[:3], 1):
                    title = article.get('title', '')
                    source = article.get('source', {}).get('name', 'Unknown')
                    published = article.get('publishedAt', '')
                    if title and title != '[Removed]' and 'removed' not in title.lower():
                        news_items.append(f"📰 {i}. {title}\n   📡 {source}")
                if news_items:
                    current_time = datetime.datetime.now().strftime('%I:%M %p')
                    news_summary = f"""📰 Top {category.title()} Headlines:
{chr(10).join(news_items)}
🕐 Updated: {current_time}
📱 Source: NewsAPI"""
                    return news_summary
                else:
                    return "❌ No valid news articles available right now."
            else:
                return f"❌ News API returned no results."
        else:
            return f"❌ News service error (Status: {response.status_code})"
    except Exception as e:
        return f"❌ News service error: {str(e)}"


  # --- Product search / recommendation helpers ---
  # PRODUCT_DATA_FILE = os.path.join(os.path.dirname(__file__), "products.json")
product_catalog = []

def load_product_catalog():
    global product_catalog
    if product_catalog:
      return product_catalog
    try:
      if os.path.exists(PRODUCT_DATA_FILE):
        with open(PRODUCT_DATA_FILE, 'r', encoding='utf-8') as f:
          product_catalog = json.load(f)
      else:
        product_catalog = []
    except Exception:
      product_catalog = []
    return product_catalog

def parse_budget_from_text(text):
    # Find first numeric value and optional 'k' multiplier (e.g., 20k -> 20000)
    m = re.search(r"(\d{1,3}(?:[\,\d]*\d)?(?:\.\d+)?)(\s*[kK])?", text)
    if not m:
      return None
    num = m.group(1).replace(',', '')
    try:
      val = float(num)
    except Exception:
      return None
    if m.group(2):
      val = val * 1000
    return int(val)

def format_product_info(p):
    price = p.get('price')
    cur = p.get('currency', 'INR')
    price_str = f"{cur} {price:,}" if isinstance(price, (int, float)) else str(price)
    rating = p.get('rating', 'N/A')
    name = p.get('name', 'Unknown')
    extra = p.get('details', '')
    return f"{name} — {price_str} — Rating: {rating}\n{extra}"

def find_products(command, max_results=3):
    load_product_catalog()
    cmd = command.lower()
    budget = parse_budget_from_text(cmd)
    # try to detect category keywords from catalog
    cats = set([p.get('category','').lower() for p in product_catalog if p.get('category')])
    category = None
    for c in cats:
      if c and c in cmd:
        category = c
        break

    # search by name tokens
    tokens = re.findall(r"[a-z0-9]+", cmd)

    candidates = []
    for p in product_catalog:
      name = p.get('name','').lower()
      cat = p.get('category','').lower()
      price = p.get('price')
      score = 0
      if category and cat == category:
        score += 20
      # match tokens in name
      for t in tokens:
        if t in name:
          score += 5
      # prefer same category words
      if category and category in name:
        score += 3
      # apply budget filter
      if budget and isinstance(price, (int, float)) and price > budget:
        continue
      # base score with rating
      rating = p.get('rating') or 0
      try:
        score += float(rating) * 2
      except Exception:
        pass
      if score > 0 or (not tokens and not category and budget is None):
        candidates.append((score, p))

    candidates.sort(key=lambda x: x[0], reverse=True)
    results = [p for s, p in candidates[:max_results]]
    return results


def get_system_info():
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count_logical = psutil.cpu_count()
        cpu_count_physical = psutil.cpu_count(logical=False)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = round(memory.used / (1024**3), 2)
        memory_total = round(memory.total / (1024**3), 2)
        memory_available = round(memory.available / (1024**3), 2)
        disk = psutil.disk_usage('/')
        disk_percent = round((disk.used / disk.total) * 100, 2)
        disk_free = round(disk.free / (1024**3), 2)
        disk_total = round(disk.total / (1024**3), 2)
        boot_time = psutil.boot_time()
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(boot_time)
        uptime_str = str(uptime).split('.')[0]
        performance_status = "🟢 Excellent"
        if cpu_percent > 80 or memory_percent > 85:
            performance_status = "🔴 High Usage"
        elif cpu_percent > 60 or memory_percent > 70:
            performance_status = "🟡 Moderate Usage"
        system_report = f"""💻 System Performance Report:
🖥️ CPU Usage: {cpu_percent}% 
   • Cores: {cpu_count_physical} physical, {cpu_count_logical} logical
   • Status: {performance_status}
🧠 Memory: {memory_percent}% used
   • Used: {memory_used}GB / Total: {memory_total}GB
   • Available: {memory_available}GB
💾 Storage: {disk_percent}% used
   • Free: {disk_free}GB / Total: {disk_total}GB
⏱️ System Uptime: {uptime_str}
🖥️ OS: {platform.system()} {platform.release()} ({platform.machine()})
🕐 Report generated: {datetime.datetime.now().strftime('%I:%M %p')}"""
        return system_report
    except Exception as e:
        return f"❌ System monitoring error: {str(e)}"

def handle_command(command):
    command_original = command
    command = command.lower().strip()
    response = ""
    emotion = "neutral"
    try:
        conversation_history.append({"user": command_original, "timestamp": datetime.datetime.now()})
        if "weather" in command:
            city = "auto"
            if "in" in command:
                parts = command.split("in")
                if len(parts) > 1:
                    city = parts[-1].strip()
            elif "for" in command:
                parts = command.split("for")
                if len(parts) > 1:
                    city = parts[-1].strip()
            response = get_weather(city)
            emotion = "calm"
            talk(response, emotion)
            return response
        elif "news" in command:
            category = "general"
            category_mapping = {
                "sports": "sports", "sport": "sports", 
                "tech": "technology", "technology": "technology",
                "business": "business", "finance": "business",
                "health": "health", "science": "science",
                "film": "film", "entertainment": "entertainment",
            }
            for key, cat in category_mapping.items():
                if key in command:
                    category = cat
                    break
            response = get_latest_news(category)
            emotion = "neutral"
            talk(response, emotion)
            return response
        elif any(word in command for word in ["system", "performance", "cpu", "memory", "disk", "pc status"]):
            response = get_system_info()
            emotion = "calm"
            talk(response, emotion)
            return response
        elif "open notepad" in command:
            response = "Opening Notepad for you! 📝"
            talk(response)
            os.system("notepad.exe")
            return response
        elif "open file" in command or "file explorer" in command or "explorer" in command:
            response = "Opening File Explorer! 📁"
            talk(response)
            os.system("explorer")
            return response
        elif "play" in command and "youtube" not in command:
            song = command.replace("play", "").strip()
            if song:
                response = f"Playing '{song}' on YouTube! 🎶"
                emotion = "excited"
                talk(response, emotion)
                try:
                    pywhatkit.playonyt(song)
                except Exception as e:
                    response = f"Sorry, couldn't play the song."
                    talk(response)
            else:
                response = "What would you like me to play? Please specify a song or artist name!"
                talk(response)
            return response
        elif "instagram" in command:
            response = "Opening Instagram for you! 📸"
            talk(response)
            webbrowser.open("https://www.instagram.com/")
            return response
        elif any(word in command for word in ["time", "what time"]):
            time_now = datetime.datetime.now().strftime('%I:%M %p')
            response = f"It's currently {time_now} ⏰"
            talk(response)
            return response
        elif any(word in command for word in ["date", "what date", "today"]):
            date_now = datetime.datetime.now().strftime('%A, %B %d, %Y')
            response = f"Today is {date_now} 📅"
            talk(response)
            return response
        elif "who is" in command:
            person = command.replace("who is", "").strip()
            if person:
                try:
                    info = wikipedia.summary(person, sentences=2)
                    response = f"Here's what I found about {person}: {info}"
                    talk(response)
                except wikipedia.exceptions.DisambiguationError as e:
                    response = f"I found multiple results for {person}. Can you be more specific?"
                    talk(response)
                except wikipedia.exceptions.PageError:
                    response = f"Sorry, I couldn't find information about {person}."
                    talk(response)
                except Exception as e:
                    response = f"I had trouble searching for {person}."
                    talk(response)
            else:
                response = "Who would you like to know about? Please specify a person's name!"
                talk(response)
            return response
        elif "joke" in command or "funny" in command:
            try:
                joke = pyjokes.get_joke()
                response = f"Here's a joke for you: {joke} 😄"
                emotion = "excited"
                talk(response, emotion)
            except Exception as e:
                jokes = [
                    "Why don't scientists trust atoms? Because they make up everything!",
                    "Why did the computer go to the doctor? Because it had a virus!",
                    "Why do programmers prefer dark mode? Because light attracts bugs!",
                    "What do you call a fake noodle? An impasta!"
                ]
                joke = random.choice(jokes)
                response = f"Here's a joke for you: {joke} 😄"
                emotion = "excited"
                talk(response, emotion)
            return response
        elif "chrome" in command:
            response = "Opening Chrome browser! 🚀"
            talk(response)
            try:
                chrome_paths = [
                    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
                ]
                opened = False
                for path in chrome_paths:
                    if os.path.exists(path):
                        os.startfile(path)
                        opened = True
                        break
                if not opened:
                    webbrowser.open("https://www.google.com")
            except Exception as e:
                webbrowser.open("https://www.google.com")
            return response
        elif "vs code" in command or "visual studio code" in command:
            response = "Opening Visual Studio Code! 💻"
            talk(response)
            try:
                os.system("code")
            except:
                response = "Visual Studio Code not found on this system."
                talk(response)
            return response
        elif "whatsapp" in command:
            response = "Opening WhatsApp Web! 📱"
            talk(response)
            webbrowser.open("https://web.whatsapp.com/")
            return response
        elif "youtube" in command and "play" not in command:
            response = "Opening YouTube! 📺"
            talk(response)
            webbrowser.open("https://www.youtube.com/")
            return response
        elif "chatgpt" in command or "chat gpt" in command:
            response = "Opening ChatGPT! 💬"
            talk(response)
            webbrowser.open("https://chat.openai.com/")
            return response
        elif "clear memory" in command or "forget" in command or "reset" in command:
            conversation_history.clear()
            response = "I've cleared my conversation memory!"
            emotion = "neutral"
            talk(response, emotion)
            return response
        elif "exit" in command or "stop" in command or "quit" in command or "goodbye" in command:
            response = "It was great talking with you! Have a wonderful day ahead! 👋"
            emotion = "excited"
            talk(response, emotion)
            return response
        else:
            response = get_ai_response(command)
            if any(word in response.lower() for word in ["great", "awesome", "excited", "amazing", "fantastic"]):
                emotion = "excited"
            elif any(word in response.lower() for word in ["sorry", "unfortunately", "problem", "error"]):
                emotion = "calm"
            talk(response, emotion)
            return response
    except Exception as e:
        error_response = f"I encountered an error: {str(e)}"
        talk(error_response)
        return error_response

def take_voice_command():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("🎤 Adjusting microphone...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("🎤 Listening...")
            audio = recognizer.listen(source, timeout=15, phrase_time_limit=10)
        print("🔄 Processing speech...")
        command = recognizer.recognize_google(audio, language='en-US')
        print("🗣 You said:", command)
        response = handle_command(command)
        return {"success": True, "command": command, "response": response}
    except sr.WaitTimeoutError:
        error_msg = "I didn't hear anything. Please try again."
        talk(error_msg)
        return {"success": False, "error": error_msg}
    except sr.UnknownValueError:
        error_msg = "I couldn't understand what you said."
        talk(error_msg)
        return {"success": False, "error": error_msg}
    except sr.RequestError as e:
        error_msg = "Speech recognition service error."
        talk(error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = "Something went wrong while listening."
        talk(error_msg)
        return {"success": False, "error": error_msg}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PANDU Assistant</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
      background-size: 400% 400%;
      animation: gradientBG 15s ease infinite;
      color: white;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 20px;
      min-height: 100vh;
    }
    @keyframes gradientBG {
      0% {background-position: 0% 50%;}
      50% {background-position: 100% 50%;}
      100% {background-position: 0% 50%;}
    }
    .header { text-align: center; margin-bottom: 20px; }
    h1 {
      margin: 0;
      font-size: 3rem;
      text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
      background: linear-gradient(45deg, #ff6ec4, #7873f5, #4ADEDE);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .status-bar {
      display: flex;
      align-items: center;
      gap: 20px;
      margin: 10px 0;
      font-size: 0.9rem;
      opacity: 0.8;
    }
    .status-indicator { display: flex; align-items: center; gap: 5px; }
    .status-dot {
      width: 8px; height: 8px; background: #2ecc71; border-radius: 50%;
      animation: pulse 2s infinite;
    }
    .status-dot.offline { background: #e74c3c; animation: none; }
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.7; transform: scale(1.1); }
    }
    .action-buttons {
      display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-bottom: 20px;
    }
    .action-btn {
      background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2);
      color: white; padding: 10px 15px; border-radius: 20px; cursor: pointer;
      transition: all 0.3s ease; backdrop-filter: blur(10px); font-size: 0.9rem;
    }
    .action-btn:hover {
      background: rgba(255,255,255,0.2); transform: translateY(-2px);
      box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .assistant-box {
      position: relative; background: rgba(255,255,255,0.1);
      border: 2px solid rgba(255,255,255,0.3); backdrop-filter: blur(12px);
      border-radius: 20px; padding: 30px; width: 100%; max-width: 800px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.3); overflow: hidden;
    }
    .assistant-box::before {
      content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
      background: conic-gradient(from 0deg, #ff6ec4, #7873f5, #4ADEDE, #ff6ec4);
      animation: rotate 8s linear infinite; z-index: -1; filter: blur(50px); opacity: 0.4;
    }
    @keyframes rotate { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .conversation-area {
      min-height: 300px; max-height: 400px; overflow-y: auto; margin-bottom: 20px;
      padding: 15px; background: rgba(0,0,0,0.1); border-radius: 15px;
      border: 1px solid rgba(255,255,255,0.1);
    }
    .conversation-item {
      margin: 10px 0; padding: 12px 15px; border-radius: 15px;
      animation: slideIn 0.3s ease; line-height: 1.4;
    }
    @keyframes slideIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .user-message {
      background: rgba(116,115,245,0.3); margin-left: 20px; border-bottom-right-radius: 5px;
    }
    .assistant-message {
      background: rgba(46,204,113,0.3); margin-right: 20px; border-bottom-left-radius: 5px;
    }
    .input-area {
      display: flex; gap: 10px; align-items: center; margin-top: 20px;
    }
    #textInput {
      flex: 1; padding: 15px 20px; font-size: 1rem; border-radius: 25px; border: none; outline: none;
      background: rgba(255,255,255,0.15); color: white; backdrop-filter: blur(10px);
      border: 1px solid rgba(255,255,255,0.2); transition: all 0.3s ease;
    }
    #textInput:focus {
      background: rgba(255,255,255,0.2); border-color: rgba(255,255,255,0.4);
      box-shadow: 0 0 20px rgba(255,255,255,0.1);
    }
    #textInput::placeholder { color: rgba(255,255,255,0.7); }
    #sendBtn {
      padding: 15px 25px; font-size: 1rem; border: none; border-radius: 25px;
      background: linear-gradient(45deg, #2ecc71, #27ae60); color: white; cursor: pointer;
      transition: all 0.3s ease; min-width: 80px;
    }
    #sendBtn:hover:not(:disabled) {
      transform: translateY(-2px); box-shadow: 0 8px 25px rgba(46,204,113,0.4);
    }
    #sendBtn:disabled { opacity: 0.5; cursor: not-allowed; }
    .mic-button {
      background: linear-gradient(45deg, #ff4757, #e84118); border: none; border-radius: 50%;
      width: 55px; height: 55px; display: flex; align-items: center; justify-content: center;
      cursor: pointer; transition: all 0.3s ease; position: relative; overflow: hidden;
    }
    .mic-button:hover {
      transform: translateY(-2px); box-shadow: 0 8px 25px rgba(255,71,87,0.4);
    }
    .mic-button.listening { animation: micPulse 1s infinite alternate; }
    .mic-button.mic-off { background: linear-gradient(45deg, #95a5a6, #7f8c8d); }
    @keyframes micPulse {
      0% { box-shadow: 0 0 0 0 rgba(255,71,87,0.7); }
      100% { box-shadow: 0 0 0 20px rgba(255,71,87,0); }
    }
    .mic-svg { width: 24px; height: 24px; fill: white; transition: all 0.3s ease; }
    .loading-spinner {
      border: 4px solid rgba(255,255,255,0.2); border-top: 4px solid #fff;
      border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite;
      margin: 20px auto; display: none;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    .controls {
      display: flex; justify-content: space-between; align-items: center;
      margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1);
    }
    .control-group { display: flex; gap: 10px; }
    .control-btn {
      background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2);
      color: white; padding: 8px 15px; border-radius: 15px; cursor: pointer;
      font-size: 0.8rem; transition: all 0.3s ease;
    }
    .control-btn:hover { background: rgba(255,255,255,0.2); }
    .error-message {
      background: rgba(231,76,60,0.9); color: white; padding: 10px 15px;
      border-radius: 10px; margin: 10px 0; display: none; animation: slideIn 0.3s ease;
    }
    .wake-word-indicator {
      position: fixed; top: 20px; right: 20px; background: rgba(255,193,7,0.9);
      color: #333; padding: 10px 15px; border-radius: 20px; font-size: 0.9rem;
      display: none; animation: slideIn 0.3s ease;
    }
    .wake-word-indicator.active { background: rgba(46,204,113,0.9); color: white; }
    @media (max-width: 768px) {
      h1 { font-size: 2.5rem; }
      .assistant-box { margin: 10px; padding: 20px; }
      .action-buttons { gap: 8px; }
      .action-btn { padding: 8px 12px; font-size: 0.8rem; }
      .input-area { flex-direction: column; gap: 15px; }
      #textInput { width: 100%; }
      .controls { flex-direction: column; gap: 10px; }
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🧠 PANDU Assistant</h1>
    <div class="status-bar">
      <div class="status-indicator">
        <div id="connectionStatus" class="status-dot"></div>
        <span id="connectionText">Online</span>
      </div>
      <div class="status-indicator">
        <span>🎤 <span id="voiceStatus">Ready</span></span>
      </div>
      <div class="status-indicator">
        <span>💬 <span id="conversationCount">0</span></span>
      </div>
    </div>
  </div>
  <div class="action-buttons">
    <button class="action-btn" onclick="quickCommand('weather')">🌤️ Weather</button>
    <button class="action-btn" onclick="quickCommand('time')">🕒 Time</button>
    <button class="action-btn" onclick="quickCommand('news')">📰 News</button>
    <button class="action-btn" onclick="quickCommand('joke')">😄 Tell Joke</button>
    <button class="action-btn" onclick="quickCommand('help')">❓ Help</button>
  </div>
  <div class="assistant-box">
    <div id="conversationArea" class="conversation-area">
      <div class="conversation-item assistant-message">
        🤖 Hello! I'm PANDU, your AI assistant. How can I help you today?
      </div>
    </div>
    <div class="error-message" id="errorMessage"></div>
    <div class="loading-spinner" id="loader"></div>
    <div class="input-area">
      <input 
        id="textInput" 
        type="text" 
        placeholder="Type your message or use voice command..." 
        onkeypress="handleKeyPress(event)"
      />
      <button id="sendBtn" onclick="sendText()">Send</button>
      <button id="micBtn" class="mic-button mic-off" onclick="toggleMic()">
        <svg class="mic-svg" viewBox="0 0 24 24">
          <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 14 0h-2zm-5 7v3h2v-3h-2z"/>
        </svg>
      </button>
    </div>
    <div class="controls">
      <div class="control-group">
        <button class="control-btn" onclick="clearConversation()">🗑️ Clear</button>
        <button class="control-btn" onclick="toggleSettings()">⚙️ Settings</button>
      </div>
      <div class="control-group">
        <button class="control-btn" onclick="exportConversation()">📤 Export</button>
        <button class="control-btn" onclick="toggleWakeWord()">🎯 Wake Word</button>
      </div>
    </div>
  </div>
  <div id="wakeWordIndicator" class="wake-word-indicator">
    Listening for "Hey PANDU"...
  </div>
  <script>
    let isListening = false;
    let wakeWordListening = false;
    let recognition = null;
    let conversationHistory = [];
    let currentVolume = 0.7;
    document.addEventListener('DOMContentLoaded', function() {
      initializeApp();
    });
    function initializeApp() {
      setupEventListeners();
      initializeSpeechRecognition();
      updateConnectionStatus(navigator.onLine);
    }
    function setupEventListeners() {
      window.addEventListener('online', () => updateConnectionStatus(true));
      window.addEventListener('offline', () => updateConnectionStatus(false));
    }
    function initializeSpeechRecognition() {
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        recognition.onstart = function() {
          updateVoiceStatus('Listening...');
        };
        recognition.onresult = function(event) {
          let finalTranscript = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
              finalTranscript += event.results[i][0].transcript;
            }
          }
          if (finalTranscript.trim()) {
            document.getElementById('textInput').value = finalTranscript.trim();
            if (isListening) {
              stopListening();
              sendText();
            }
          }
        };
        recognition.onerror = function(event) {
          showError('Speech recognition error: ' + event.error);
          stopListening();
        };
        recognition.onend = function() {
          if (isListening) {
            stopListening();
          }
        };
      } else {
        showError('Speech recognition not supported in this browser');
      }
    }
    function handleKeyPress(event) {
      if (event.key === 'Enter') {
        sendText();
      }
    }
    function sendText() {
      const text = document.getElementById("textInput").value.trim();
      if (!text) return;
      addToConversation(text, true);
      showLoading(true);
      updateVoiceStatus('Processing...');
      fetch('/text-command', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({command: text})
      })
      .then(response => response.json())
      .then(data => {
        showLoading(false);
        updateVoiceStatus('Ready');
        addToConversation(data.response);
        speakText(data.response);
        document.getElementById("textInput").value = "";
      })
      .catch(err => {
        showLoading(false);
        updateVoiceStatus('Error');
        const errorMsg = "Sorry, I'm having trouble processing your request. Please try again.";
        addToConversation(errorMsg);
        showError(err.message);
      });
    }
    function toggleMic() {
      if (isListening) {
        stopListening();
      } else {
        startListening();
      }
    }
    function startListening() {
      if (!recognition) {
        showError('Speech recognition not available');
        return;
      }
      isListening = true;
      const micBtn = document.getElementById("micBtn");
      micBtn.classList.remove("mic-off");
      micBtn.classList.add("listening");
      updateVoiceStatus('Listening...');
      try {
        recognition.start();
      } catch (e) {
        stopListening();
        showError('Could not start voice recognition');
      }
    }
    function stopListening() {
      isListening = false;
      const micBtn = document.getElementById("micBtn");
      micBtn.classList.add("mic-off");
      micBtn.classList.remove("listening");
      updateVoiceStatus('Ready');
      if (recognition) {
        recognition.stop();
      }
    }
    function speakText(text) {
      if ('speechSynthesis' in window) {
        speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.volume = currentVolume;
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        const voices = speechSynthesis.getVoices();
        const preferredVoice = voices.find(voice => 
          voice.name.includes('Google') || 
          voice.name.includes('Microsoft') ||
          voice.lang.startsWith('en')
        );
        if (preferredVoice) {
          utterance.voice = preferredVoice;
        }
        speechSynthesis.speak(utterance);
      }
    }
    function addToConversation(message, isUser = false) {
      const conversationArea = document.getElementById('conversationArea');
      const conversationItem = document.createElement('div');
      conversationItem.className = `conversation-item ${isUser ? 'user-message' : 'assistant-message'}`;
      conversationItem.innerHTML = `${isUser ? '👤' : '🤖'} ${message}`;
      conversationArea.appendChild(conversationItem);
      conversationArea.scrollTop = conversationArea.scrollHeight;
      conversationHistory.push({message, isUser, timestamp: new Date()});
      document.getElementById('conversationCount').textContent = conversationHistory.length;
    }
    function quickCommand(command) {
      const commands = {
        weather: "What's the weather like today?",
        time: "What time is it?",
        news: "Tell me the latest news",
        joke: "Tell me a joke",
        help: "What can you help me with?"
      };
      document.getElementById('textInput').value = commands[command] || command;
      sendText();
    }
    function clearConversation() {
      if (confirm('Clear conversation history?')) {
        const conversationArea = document.getElementById('conversationArea');
        conversationArea.innerHTML = `
          <div class="conversation-item assistant-message">
            🤖 Conversation cleared. How can I help you?
          </div>
        `;
        conversationHistory = [];
        document.getElementById('conversationCount').textContent = '0';
      }
    }
    function exportConversation() {
      if (conversationHistory.length === 0) {
        showError('No conversation to export');
        return;
      }
      const exportData = conversationHistory.map(item => 
        `${item.isUser ? 'User' : 'Assistant'}: ${item.message}`
      ).join('\\n\\n');
      const blob = new Blob([exportData], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `pandu-conversation-${new Date().toISOString().split('T')[0]}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    }
    function toggleSettings() {
      const settings = [
        '⚙️ Settings (Demo)',
        '',
        '• Voice Settings',
        '• Language: English',
        '• Speech Rate: 0.9x',
        '• Volume: 70%',
        '',
        '• Display Settings',
        '• Theme: Gradient',
        '• Animations: Enabled',
        '',
        '• Privacy Settings',
        '• Save Conversations: No',
        '• Analytics: Disabled'
      ].join('\\n');
      alert(settings);
    }
    function toggleWakeWord() {
      wakeWordListening = !wakeWordListening;
      const indicator = document.getElementById('wakeWordIndicator');
      if (wakeWordListening) {
        indicator.style.display = 'block';
        indicator.textContent = 'Listening for "Hey PANDU"...';
        startWakeWordListening();
      } else {
        indicator.style.display = 'none';
        stopWakeWordListening();
      }
    }
    function startWakeWordListening() {
      if (!recognition || !wakeWordListening) return;
      setTimeout(() => {
        if (wakeWordListening) {
          startWakeWordListening();
        }
      }, 5000);
    }
    function stopWakeWordListening() {
      wakeWordListening = false;
    }
    function updateConnectionStatus(isOnline) {
      const statusDot = document.getElementById('connectionStatus');
      const statusText = document.getElementById('connectionText');
      if (isOnline) {
        statusDot.classList.remove('offline');
        statusText.textContent = 'Online';
      } else {
        statusDot.classList.add('offline');
        statusText.textContent = 'Offline';
      }
    }
    function updateVoiceStatus(status) {
      document.getElementById('voiceStatus').textContent = status;
    }
    function showLoading(show) {
      document.getElementById("loader").style.display = show ? "block" : "none";
      document.getElementById("sendBtn").disabled = show;
    }
    function showError(message) {
      const errorDiv = document.getElementById('errorMessage');
      errorDiv.textContent = message;
      errorDiv.style.display = 'block';
      setTimeout(() => {
        errorDiv.style.display = 'none';
      }, 5000);
    }
    if ('speechSynthesis' in window) {
      speechSynthesis.addEventListener('voiceschanged', function() {});
    }
  </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start-voice', methods=['POST'])
def start_voice():
    try:
        result = take_voice_command()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/text-command', methods=['POST'])
def text_command():
    try:
        data = request.get_json()
        command = data.get('command', '')
        if not command:
            return jsonify({"response": "No command received"})
        response = handle_command(command)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})

if __name__ == '__main__':
    print("🤖 PANDU AI Voice Assistant Server Starting...")
    print("🌐 Open your browser and go to: http://localhost:5000")
    talk("Hello! I'm voice assistant. Server is starting!", "excited")
    app.run(debug=True, host='0.0.0.0', port=5000)