from dotenv import load_dotenv
import os
import datetime
import requests
import re
import random
import holidays
import urllib.parse
import math
import webbrowser
import pyautogui
import time
import speech_recognition as sr
import pyttsx3
import pywhatkit as kit
from deep_translator import GoogleTranslator
from openai import OpenAI



load_dotenv()
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HF_TOKEN"],
)



voice_engine = None
recognizer = None
mic = None



class ChatSessionState:
    def __init__(self):
        self.quiz_state = {"active": False, "question": None, "answer": None, "awaiting_continue": False}
        self.guess_state = {"active": False, "number": None, "attempts": 0, "max_attempts": 5, "awaiting_continue": False}
        self.voice_mode = {"active": False, "current_website": None}



chat_sessions = {}



def get_chat_state(chat_id):
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = ChatSessionState()
    return chat_sessions[chat_id]



def init_voice():
    global voice_engine, recognizer, mic
    if voice_engine is None:
        voice_engine = pyttsx3.init()
    if recognizer is None:
        recognizer = sr.Recognizer()
    if mic is None:
        try:
            mic = sr.Microphone()
        except:
            mic = None
            print("⚠️ Mic not available, voice features disabled")



def speak(text):
    if voice_engine is None:
        init_voice()
    try:
        print(f"🔊 Jarvis: {text}")
        voice_engine.say(text)
        voice_engine.runAndWait()
    except:
        print(f"🔊 Jarvis: {text}")



def listen():
    if mic is None:
        return None
    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("🎤 Listening...")
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
        try:
            query = recognizer.recognize_google(audio).lower()
            print(f"👤 You said: {query}")
            return query
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            return None
    except:
        return None



KNOWN_SITES = {
# 🔍 Search Engines
"google": "https://www.google.com",
"bing": "https://www.bing.com",
"duckduckgo": "https://duckduckgo.com",
"yahoo": "https://search.yahoo.com",

# 🎥 Entertainment
"youtube": "https://www.youtube.com",
"netflix": "https://www.netflix.com",
"prime video": "https://www.primevideo.com",
"hotstar": "https://www.hotstar.com",
"spotify": "https://open.spotify.com",
"soundcloud": "https://soundcloud.com",

# 📱 Social Media
"facebook": "https://www.facebook.com",
"instagram": "https://www.instagram.com",
"twitter": "https://twitter.com",
"x": "https://twitter.com",
"linkedin": "https://www.linkedin.com",
"reddit": "https://www.reddit.com",
"pinterest": "https://www.pinterest.com",
"snapchat": "https://www.snapchat.com",
"threads": "https://www.threads.net",

# 💻 Developer & Coding
"github": "https://github.com",
"gitlab": "https://gitlab.com",
"stack overflow": "https://stackoverflow.com",
"leetcode": "https://leetcode.com",
"codeforces": "https://codeforces.com",
"hacker rank": "https://www.hackerrank.com",
"geeksforgeeks": "https://www.geeksforgeeks.org",
"w3schools": "https://www.w3schools.com",
"freecodecamp": "https://www.freecodecamp.org",
"replit": "https://replit.com",
"codesandbox": "https://codesandbox.io",

# 🤖 AI Tools
"chatgpt": "https://chat.openai.com",
"openai": "https://openai.com",
"claude": "https://claude.ai",
"gemini": "https://gemini.google.com",
"perplexity": "https://www.perplexity.ai",
"midjourney": "https://www.midjourney.com",
"runway": "https://runwayml.com",

# 📚 Study & Learning
"wikipedia": "https://www.wikipedia.org",
"coursera": "https://www.coursera.org",
"udemy": "https://www.udemy.com",
"edx": "https://www.edx.org",
"khan academy": "https://www.khanacademy.org",
"byjus": "https://byjus.com",
"unacademy": "https://unacademy.com",
"vedantu": "https://www.vedantu.com",
"toppr": "https://www.toppr.com",

# 📖 Notes & Docs
"notion": "https://www.notion.so",
"evernote": "https://evernote.com",
"google docs": "https://docs.google.com",
"google drive": "https://drive.google.com",
"dropbox": "https://www.dropbox.com",

# 🛒 Shopping
"amazon": "https://www.amazon.in",
"flipkart": "https://www.flipkart.com",
"myntra": "https://www.myntra.com",
"ajio": "https://www.ajio.com",
"meesho": "https://www.meesho.com",

# 💼 Jobs & Career
"naukri": "https://www.naukri.com",
"indeed": "https://www.indeed.com",
"glassdoor": "https://www.glassdoor.com",
"internshala": "https://internshala.com",

# 💬 Communication
"gmail": "https://mail.google.com",
"outlook": "https://outlook.live.com",
"whatsapp web": "https://web.whatsapp.com",
"telegram": "https://web.telegram.org",
"zoom": "https://zoom.us",

# 🌐 Utilities
"speed test": "https://www.speedtest.net",
"canva": "https://www.canva.com",
"remove bg": "https://www.remove.bg",
"tiny url": "https://tinyurl.com",
"ilovepdf": "https://www.ilovepdf.com",

# 💰 Finance
"paytm": "https://paytm.com",
"phonepe": "https://www.phonepe.com",
"gpay": "https://pay.google.com",
"zerodha": "https://zerodha.com",
"groww": "https://groww.in",

# 📰 News
"bbc": "https://www.bbc.com",
"cnn": "https://www.cnn.com",
"ndtv": "https://www.ndtv.com",
"times of india": "https://timesofindia.indiatimes.com",
"hindustan times": "https://www.hindustantimes.com",

# 🎮 Gaming
"steam": "https://store.steampowered.com",
"epic games": "https://www.epicgames.com",
"twitch": "https://www.twitch.tv",

# 🧠 Productivity
"trello": "https://trello.com",
"asana": "https://asana.com",
"clickup": "https://clickup.com",

# 🧪 Tech & Tools
"postman": "https://www.postman.com",
"figma": "https://www.figma.com",
"adobe": "https://www.adobe.com",

# 🌍 Travel
"booking": "https://www.booking.com",
"makemytrip": "https://www.makemytrip.com",
"goibibo": "https://www.goibibo.com",
"airbnb": "https://www.airbnb.com",

# 🎓 Extra Study (High Quality)
"mit ocw": "https://ocw.mit.edu",
"stanford online": "https://online.stanford.edu",
"harvard online": "https://online-learning.harvard.edu",
"nptel": "https://nptel.ac.in",

# 🧑‍💻 APIs & Dev Tools
"rapidapi": "https://rapidapi.com",
"firebase": "https://firebase.google.com",
"vercel": "https://vercel.com",
"netlify": "https://www.netlify.com"
}



def clean_site_name(site_name):
    site_name = site_name.lower().strip()
    site_name = re.sub(r"^(open|search|go to|visit)\s+", "", site_name).strip()
    site_name = re.sub(r"\s+(website|site|app)$", "", site_name).strip()
    return site_name



def extract_site_from_query(query):
    """Extract site name from 'open <site>' type queries only"""
    query = query.lower().strip()

    patterns = [
        r"^open\s+(.+)",
        r"^go to\s+(.+)",
        r"^visit\s+(.+)",
    ]

    for pattern in patterns:
        match = re.match(pattern, query)
        if match:
            raw = match.group(1).strip()
            raw = re.sub(r"\s+(website|site|app)$", "", raw).strip()
            return raw

    return None



def open_url(url):
    try:
        webbrowser.open_new_tab(url)
        return True
    except:
        try:
            webbrowser.open(url, new=2)
            return True
        except:
            return False



def google_search_query(query):
    """Normal Google search for any query"""
    try:
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        open_url(search_url)
        return True
    except:
        return False



def open_site_by_name(site_name):
    """Opens a known site directly, or constructs https URL, or Google search"""
    site_name_clean = site_name.lower().strip()

    # KNOWN_SITES → direct URL
    if site_name_clean in KNOWN_SITES:
        open_url(KNOWN_SITES[site_name_clean])
        return site_name_clean

    # Has a dot and no spaces → treat as direct URL
    if "." in site_name_clean and " " not in site_name_clean:
        test_url = site_name_clean if site_name_clean.startswith("http") else f"https://{site_name_clean}"
        open_url(test_url)
        return site_name_clean

    # Unknown site → Google search (NOT I'm Feeling Lucky redirect)
    google_search_query(site_name_clean)
    return site_name_clean



def focus_browser():
    try:
        pyautogui.click(x=500, y=200)
        time.sleep(0.2)
    except:
        pass



def close_current_tab():
    try:
        focus_browser()
        pyautogui.hotkey('ctrl', 'w')
        time.sleep(0.4)
        return True
    except:
        return False



def open_website_and_listen(url, site_name):
    init_voice()
    speak(f"Opening {site_name}...")
    open_url(url)
    time.sleep(4)

    state = get_chat_state("voice")
    state.voice_mode["active"] = True
    state.voice_mode["current_website"] = site_name

    speak("Website opened. Say what to search or play, or say 'back' to return.")

    while state.voice_mode["active"]:
        query = listen()
        if not query:
            continue

        if any(word in query for word in ["back", "close", "exit", "return"]):
            speak("Closing website. Back to Jarvis chat.")
            close_current_tab()
            state.voice_mode["active"] = False
            state.voice_mode["current_website"] = None
            break

        handle_voice_website_action(query, site_name)

    return "Website closed. How can I help you now?"



def open_dynamic_website_and_listen(site_name):
    init_voice()
    speak(f"Opening {site_name}...")

    opened_name = open_site_by_name(site_name)
    time.sleep(5)

    state = get_chat_state("voice")
    state.voice_mode["active"] = True
    state.voice_mode["current_website"] = opened_name

    speak("Website opened. Say search something, play on youtube, or say back to return.")

    while state.voice_mode["active"]:
        query = listen()
        if not query:
            continue

        if any(word in query for word in ["back", "close", "exit", "return"]):
            speak("Closing website. Back to Jarvis chat.")
            close_current_tab()
            state.voice_mode["active"] = False
            state.voice_mode["current_website"] = None
            break

        handle_voice_website_action(query, opened_name)

    return "Website closed. How can I help you now?"



def extract_search_term(query):
    query = query.strip()

    patterns = [
        r"^(search for)\s+",
        r"^(search)\s+",
        r"^(find)\s+",
        r"^(look up)\s+",
        r"^(play)\s+",
    ]

    for pattern in patterns:
        query = re.sub(pattern, "", query, flags=re.IGNORECASE).strip()

    query = re.sub(r"\s+(on youtube|on google|on wikipedia|on github)$", "", query, flags=re.IGNORECASE).strip()
    return query



def search_inside_current_website(search_term):
    if not search_term:
        speak("What should I search?")
        return

    try:
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.write(search_term, interval=0.03)
        pyautogui.press('enter')
        speak(f"Searching {search_term}")
    except:
        speak("Sorry, I could not search on this website.")



def youtube_search_only(search_term):
    if not search_term:
        speak("What should I search on YouTube?")
        return
    try:
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_term)}"
        open_url(search_url)
        speak(f"Searching {search_term} on YouTube")
    except:
        speak("Sorry, I could not search on YouTube.")



def youtube_play_direct(search_term):
    if not search_term:
        search_term = "music"
    try:
        speak(f"Playing {search_term} on YouTube")
        kit.playonyt(search_term)
    except:
        speak("Sorry, I could not play that on YouTube.")



def github_search(search_term):
    if not search_term:
        speak("What should I search on GitHub?")
        return
    try:
        search_url = f"https://github.com/search?q={urllib.parse.quote(search_term)}"
        open_url(search_url)
        speak(f"Searching {search_term} on GitHub")
    except:
        speak("Sorry, I could not search on GitHub.")



def handle_voice_website_action(query, site_name):
    query = query.lower().strip()

    if site_name == "youtube":
        if query.startswith("play "):
            search_term = extract_search_term(query)
            youtube_play_direct(search_term)
            return

        if any(query.startswith(cmd) for cmd in ["search ", "search for ", "find ", "look up "]):
            search_term = extract_search_term(query)
            youtube_search_only(search_term)
            return

    elif site_name == "github":
        if any(query.startswith(cmd) for cmd in ["search ", "search for ", "find ", "look up "]):
            search_term = extract_search_term(query)
            github_search(search_term)
            return

    elif site_name == "wikipedia":
        if any(query.startswith(cmd) for cmd in ["search ", "search for ", "find ", "look up "]):
            search_term = extract_search_term(query)
            search_inside_current_website(search_term)
            speak(f"Searching {search_term} on Wikipedia")
            return

    elif site_name == "google":
        if any(query.startswith(cmd) for cmd in ["search ", "search for ", "find ", "look up "]):
            search_term = extract_search_term(query)
            search_inside_current_website(search_term)
            speak(f"Searching for {search_term} on Google")
            return

    else:
        if any(query.startswith(cmd) for cmd in ["search ", "search for ", "find ", "look up "]):
            search_term = extract_search_term(query)
            search_inside_current_website(search_term)
            return

        search_inside_current_website(query)
        return



def clean_ai_response(text):
    if not text:
        return "Sorry, I could not generate a proper response."

    text = text.strip()

    text = re.sub(r'\bs+r+y+\b', 'Sorry', text, flags=re.IGNORECASE)
    text = re.sub(r'\biam\b', 'I am', text, flags=re.IGNORECASE)
    text = re.sub(r"\bim\b", "I'm", text, flags=re.IGNORECASE)
    text = re.sub(r"\bidont\b", "I don't", text, flags=re.IGNORECASE)
    text = re.sub(r"\bcant\b", "can't", text, flags=re.IGNORECASE)
    text = re.sub(r"\bdont\b", "don't", text, flags=re.IGNORECASE)
    text = re.sub(r"\bdoesnt\b", "doesn't", text, flags=re.IGNORECASE)
    text = re.sub(r"\bwont\b", "won't", text, flags=re.IGNORECASE)
    text = re.sub(r"\bcouldnt\b", "couldn't", text, flags=re.IGNORECASE)
    text = re.sub(r"\bshouldnt\b", "shouldn't", text, flags=re.IGNORECASE)
    text = re.sub(r"\bwouldnt\b", "wouldn't", text, flags=re.IGNORECASE)

    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    if text and text[0].islower():
        text = text[0].upper() + text[1:]

    return text.strip()



def get_greeting():
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"



def handle_greeting(query):
    query = query.lower().strip()
    if query in ["hello", "hi", "hey", "jarvis"]:
        greeting = get_greeting()
        return f"{greeting}! How can I assist you?"
    return None



def handle_search_command(query):
    """
    Handle 'search <something>' from chat or voice (NOT inside a website).
    Always opens a normal Google search.
    Only triggers when NOT inside a website session.
    """
    q = query.lower().strip()

    # Must start with 'search' keyword
    if not (q.startswith("search ") or q.startswith("search for ")):
        return None

    # Extract what to search
    search_term = re.sub(r"^search for\s+", "", q, flags=re.IGNORECASE).strip()
    search_term = re.sub(r"^search\s+", "", search_term, flags=re.IGNORECASE).strip()

    if not search_term:
        return "What do you want me to search?"

    google_search_query(search_term)
    return f"🔍 Searching Google for: {search_term}"



def handle_voice_commands(query):
    query_lower = query.lower().strip()

    # open + KNOWN site → open directly with voice loop
    if query_lower.startswith("open "):
        site_name = extract_site_from_query(query_lower)
        if site_name:
            site_clean = site_name.lower().strip()
            if site_clean in KNOWN_SITES:
                return open_website_and_listen(KNOWN_SITES[site_clean], site_clean)
            else:
                # Unknown site → open_dynamic (which does Google search for unknown sites)
                return open_dynamic_website_and_listen(site_clean)

    elif query_lower.startswith("go to ") or query_lower.startswith("visit "):
        site_name = extract_site_from_query(query_lower)
        if site_name:
            return open_dynamic_website_and_listen(site_name)

    elif any(word in query_lower for word in ["voice mode", "voice control"]):
        init_voice()
        speak("Voice mode activated. Say open youtube, open wikipedia, or ask me to open any website.")
        return "Voice mode ready"

    return None



def get_random_quote():
    try:
        response = requests.get("https://zenquotes.io/api/random", timeout=10)
        data = response.json()
        quote_data = data[0]
        text = quote_data["q"]
        author = quote_data["a"]
        return f'💡 "{text}" — {author}'
    except Exception:
        return "Sorry, couldn't fetch a quote right now."



def handle_quote(query):
    query = query.lower()
    if any(word in query for word in ["quote", "motivation", "inspire"]):
        return get_random_quote()
    return None



def get_holidays(country_code="IN", year=None):
    if not year:
        year = datetime.date.today().year
    try:
        country_holidays = holidays.CountryHoliday(country_code, years=year)
        if not country_holidays:
            return f"No holidays found for {country_code} in {year}."
        holiday_list = []
        for date, name in sorted(country_holidays.items()):
            holiday_list.append(f"{date}: {name}")
        full_list = "\n".join(holiday_list)
        return f"📅 Holidays in {country_code} ({year}):\n{full_list}"
    except Exception as e:
        return f"Error fetching holidays: {e}"



def handle_holidays(query):
    query = query.lower()
    if "holiday" in query:
        country = "IN"
        year = datetime.date.today().year
        match = re.search(r"\b(20\d{2})\b", query)
        if match:
            year = int(match.group(1))
        if "us" in query or "america" in query:
            country = "US"
        elif "uk" in query:
            country = "GB"
        elif "india" in query:
            country = "IN"
        return get_holidays(country, year)
    return None



def get_short_wikipedia_summary(topic, lang="en"):
    headers = {"User-Agent": "JarvisBot/1.0"}
    search_url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": topic,
        "format": "json",
        "utf8": 1,
        "srlimit": 1
    }
    try:
        search_resp = requests.get(search_url, headers=headers, params=params, timeout=10)
        search_data = search_resp.json()
        results = search_data.get("query", {}).get("search", [])
        if not results:
            return f"No Wikipedia page found for {topic}"
        title = results[0]["title"]
        encoded_title = urllib.parse.quote(title.replace(" ", "_"))
        summary_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
        summary_resp = requests.get(summary_url, headers=headers, timeout=10)
        summary_data = summary_resp.json()
        extract = summary_data.get("extract", "No summary available")
        extract = extract.encode('latin1').decode('utf-8', 'replace').strip()
        return f"📖 {title}\n\n{extract}"
    except Exception:
        return "Error fetching Wikipedia data"



def handle_wikipedia(query):
    query = query.lower()
    if "wikipedia" in query or "who is" in query or "what is" in query:
        topic = query.replace("wikipedia", "").replace("who is", "").replace("what is", "").strip()
        if topic:
            return get_short_wikipedia_summary(topic)
    return None



def get_movie_info(movie_name):
    try:
        api_key = "3e5458a"
        url = f"http://www.omdbapi.com/?t={urllib.parse.quote(movie_name)}&apikey={api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data["Response"] == "False":
            return f"❌ Movie not found: {movie_name}"
        title = data.get("Title", "N/A")
        year = data.get("Year", "N/A")
        genre = data.get("Genre", "N/A")
        plot = data.get("Plot", "No description available.")
        imdb_rating = data.get("imdbRating", "N/A")
        actors = data.get("Actors", "N/A")
        director = data.get("Director", "N/A")
        return (
            f"🎬 {title} ({year})\n"
            f"🎭 Genre: {genre}\n"
            f"⭐ IMDb Rating: {imdb_rating}\n"
            f"🎥 Director: {director}\n"
            f"👥 Cast: {actors}\n"
            f"📖 Plot: {plot}"
        )
    except Exception as e:
        return f"Error fetching movie info: {e}"



def handle_movie(query):
    query = query.lower()
    if "movie" in query or "film" in query:
        match = re.search(r"(movie|film)\s+(.*)", query)
        if match:
            movie = match.group(2).strip()
        else:
            return "Please tell me the movie name."
        return get_movie_info(movie)
    return None



quiz_questions = {
    "What is the capital of India?": "delhi",
    "What is the capital of Japan?": "tokyo",
    "What is the capital of USA?": "washington dc",
    "What is the capital of Germany?": "berlin",
    "What is the capital of Canada?": "ottawa",
    "What is 10 + 5?": "15",
    "What is 12 - 7?": "5",
    "What is 9 x 9?": "81",
    "What is 100 divided by 4?": "25",
    "What is 7 x 8?": "56",
    "How many days are there in a week?": "7",
    "How many months are there in a year?": "12",
    "How many hours in a day?": "24",
    "How many minutes in an hour?": "60",
    "How many seconds in a minute?": "60",
    "What color is the sky?": "blue",
    "What color are bananas?": "yellow",
    "What color is grass?": "green",
    "What color is coal?": "black",
    "What color is milk?": "white",
    "What is the largest planet?": "jupiter",
    "What planet is closest to the sun?": "mercury",
    "What planet do we live on?": "earth",
    "What is the smallest planet?": "mercury",
    "What planet has rings?": "saturn",
    "How many continents are there?": "7",
    "What is the largest ocean?": "pacific",
    "What is the longest river?": "nile",
    "What is the tallest mountain?": "everest",
    "What is the fastest land animal?": "cheetah",
    "What is the national animal of India?": "tiger",
    "What is the national bird of India?": "peacock",
    "What is the national fruit of India?": "mango",
    "What is the national flower of India?": "lotus",
    "What is the national sport of India?": "hockey",
    "What gas do plants take in?": "carbon dioxide",
    "What gas do humans breathe in?": "oxygen",
    "What is H2O?": "water",
    "What is the boiling point of water?": "100",
    "What is the freezing point of water?": "0",
    "Who invented the light bulb?": "edison",
    "Who discovered gravity?": "newton",
    "Who is known as the father of computers?": "babbage",
    "Who wrote the Ramayana?": "valmiki",
    "Who wrote the Mahabharata?": "vyasa",
    "What is 15 x 2?": "30",
    "What is 20 + 30?": "50",
    "What is 50 - 25?": "25",
    "What is 6 x 7?": "42",
    "What is 81 divided by 9?": "9",
    "What is the square of 5?": "25",
    "What is the square of 10?": "100",
    "What is the cube of 3?": "27",
    "What is the cube of 2?": "8",
    "What is 11 x 11?": "121",
    "Which animal is known as king of jungle?": "lion",
    "Which animal is the largest mammal?": "blue whale",
    "Which bird can mimic human speech?": "parrot",
    "Which animal has a long trunk?": "elephant",
    "Which animal is known for hopping?": "kangaroo",
    "What is the currency of India?": "rupee",
    "What is the currency of USA?": "dollar",
    "What is the currency of UK?": "pound",
    "What is the currency of Japan?": "yen",
    "What is the currency of Europe?": "euro",
    "What is the opposite of hot?": "cold",
    "What is the opposite of big?": "small",
    "What is the opposite of fast?": "slow",
    "What is the opposite of happy?": "sad",
    "What is the opposite of light?": "dark",
    "What shape has 3 sides?": "triangle",
    "What shape has 4 equal sides?": "square",
    "What shape is round?": "circle",
    "What shape has 5 sides?": "pentagon",
    "What shape has 6 sides?": "hexagon",
    "How many vowels are in English?": "5",
    "How many letters are in English alphabet?": "26",
    "What is the first letter of alphabet?": "a",
    "What is the last letter of alphabet?": "z",
    "What comes after b?": "c",
    "What comes before y?": "x",
    "What is 1000 divided by 10?": "100",
    "What is 25 x 4?": "100",
    "What is 90 divided by 3?": "30",
    "What is 14 + 6?": "20",
    "What is 45 - 15?": "30",
    "What is the capital of Australia?": "canberra",
    "What is the capital of China?": "beijing",
    "What is the capital of Russia?": "moscow",
    "What is the capital of Italy?": "rome",
    "What is the capital of Spain?": "madrid",
    "What is the capital of Brazil?": "brasilia",
    "What is the capital of South Korea?": "seoul",
    "What is the capital of UAE?": "abu dhabi",
    "What is the capital of Nepal?": "kathmandu",
    "What is the capital of Sri Lanka?": "colombo"
}



def get_random_question():
    q, a = random.choice(list(quiz_questions.items()))
    return q, a



def handle_quiz(query, chat_id):
    state = get_chat_state(chat_id)
    query = query.lower().strip()

    if "quiz" in query and not state.quiz_state["active"]:
        q, a = get_random_question()
        state.quiz_state.update({"active": True, "question": q, "answer": a, "awaiting_continue": False})
        return f"🎯 Quiz Time!\n\n{q}"

    if state.quiz_state["active"]:
        if not state.quiz_state["awaiting_continue"]:
            if query == state.quiz_state["answer"]:
                response = "✅ Correct!"
            else:
                response = f"❌ Wrong! Correct answer was {state.quiz_state['answer']}"
            state.quiz_state["awaiting_continue"] = True
            return response + "\n\nDo you want another question? (yes/no)"
        else:
            if query in ["yes", "y"]:
                q, a = get_random_question()
                state.quiz_state.update({"question": q, "answer": a, "awaiting_continue": False})
                return f"🎯 Next Question:\n\n{q}"
            elif query in ["no", "n"]:
                state.quiz_state = {"active": False, "question": None, "answer": None, "awaiting_continue": False}
                return "👍 Okay! See you next time for quiz."
            else:
                return "Please answer with yes or no."
    return None



def handle_guess_number(query, chat_id):
    state = get_chat_state(chat_id)
    query = query.lower().strip()

    if "guess" in query and "number" in query and not state.guess_state["active"]:
        state.guess_state = {
            "active": True,
            "number": random.randint(1, 50),
            "attempts": 0,
            "max_attempts": 5,
            "awaiting_continue": False
        }
        return "🎯 I have chosen a number between 1 and 50. Try to guess it! You have 5 chances"

    if state.guess_state["active"]:
        if state.guess_state["awaiting_continue"]:
            if query in ["yes", "y"]:
                state.guess_state = {
                    "active": True,
                    "number": random.randint(1, 50),
                    "attempts": 0,
                    "max_attempts": 5,
                    "awaiting_continue": False
                }
                return "🎯 New game started! Guess the number (1–50)."
            elif query in ["no", "n"]:
                state.guess_state["active"] = False
                return "👍 Okay! See you next time."
            else:
                return "Please answer with yes or no."

        try:
            guess = int(query)
        except Exception:
            return "Please enter a valid number."

        state.guess_state["attempts"] += 1
        if guess == state.guess_state["number"]:
            state.guess_state["awaiting_continue"] = True
            return "🎉 Correct! You guessed it right!\n\nPlay again? (yes/no)"
        elif guess < state.guess_state["number"]:
            msg = "Too low!"
        else:
            msg = "Too high!"

        if state.guess_state["attempts"] >= state.guess_state["max_attempts"]:
            num = state.guess_state["number"]
            state.guess_state["awaiting_continue"] = True
            return f"❌ Game over! The number was {num}.\n\nPlay again? (yes/no)"

        return msg
    return None



def calculate_expression(expression):
    try:
        expression = expression.lower()
        expression = expression.replace("plus", "+").replace("add", "+")
        expression = expression.replace("minus", "-").replace("subtract", "-")
        expression = expression.replace("multiply", "*").replace("times", "*").replace("into", "*")
        expression = expression.replace("divide", "/").replace("by", "/")
        expression = expression.replace("power", "**").replace("raised to", "**")
        expression = expression.replace("square root of", "math.sqrt(")
        if "math.sqrt(" in expression and not expression.endswith(")"):
            expression += ")"
        expression = re.sub(r"\s+", "", expression)
        result = eval(expression, {"__builtins__": None, "math": math})
        return f"The result is {result}"
    except Exception:
        return "Sorry, I couldn't calculate that."



def handle_calculator(query):
    query = query.lower()
    if any(word in query for word in ["calculate", "+", "-", "*", "/", "multiply", "divide", "plus"]):
        expression = query.replace("calculate", "").strip()
        return calculate_expression(expression)
    return None



def translate_text(text, target_language="hi"):
    try:
        translated = GoogleTranslator(source="auto", target=target_language).translate(text)
        return translated
    except Exception:
        return "Error in translation"



def handle_translate(query):
    query = query.lower()
    if "translate" in query:
        text = query.replace("translate", "").strip()
        if not text:
            return "What do you want me to translate?"
        translated = translate_text(text)
        return f"🌐 Translation:\n{translated}"
    return None



def handle_huggingface_ai(query):
    try:
        system_prompt = (
            "You are Jarvis, a friendly yet professional AI assistant. "
            "Respond clearly, naturally, and helpfully. "
            "Use 0-1 emoji MAXIMUM per response. NO emoji spam. "
            "Give best answer in a concise manner."
            "Use emojis only when they fit naturally. "
            "When useful, ask a short relevant follow-up question."
        )
        completion = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.2:featherless-ai",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            max_tokens=700,
            temperature=0.5
        )
        raw_text = completion.choices[0].message.content.strip()
        return clean_ai_response(raw_text)
    except Exception:
        return clean_ai_response("Sorry, the AI is unavailable right now. Please try again later.")



def run_jarvis(query, chat_id):
    # 1. Voice/Open commands (open youtube, go to github, etc.)
    response = handle_voice_commands(query)
    if response:
        return response

    # 2. Quiz
    response = handle_quiz(query, chat_id)
    if response:
        return response

    # 3. Number guessing game
    response = handle_guess_number(query, chat_id)
    if response:
        return response

    # 4. Movie info
    response = handle_movie(query)
    if response:
        return response

    # 5. Wikipedia
    response = handle_wikipedia(query)
    if response:
        return response

    # 6. Quote
    response = handle_quote(query)
    if response:
        return response

    # 7. Holidays
    response = handle_holidays(query)
    if response:
        return response

    # 8. Translate
    response = handle_translate(query)
    if response:
        return response

    # 9. Calculator
    response = handle_calculator(query)
    if response:
        return response

    # 10. 'search <query>' from chat → normal Google search
    response = handle_search_command(query)
    if response:
        return response

    # 11. Greeting
    response = handle_greeting(query)
    if response:
        return response

    # 12. AI fallback
    return handle_huggingface_ai(query)



def voice_mode():
    init_voice()
    speak("Jarvis voice mode activated. Say open youtube, open wikipedia, open any website, voice mode off, or ask anything.")
    while True:
        query = listen()
        if not query:
            continue
        if any(word in query for word in ["voice mode off", "stop voice", "exit voice"]):
            speak("Voice mode deactivated.")
            break
        response = run_jarvis(query, "voice")
        speak(response)



if __name__ == "__main__":
    print("🎙️ Jarvis Voice Bot Ready! (Fixed Version)")
    print("✅ Text mode: Type normally")
    print("✅ Voice mode: Type 'voice mode' then speak")
    print("✅ Open sites: 'open youtube', 'open instagram', 'open chrome web store'")
    print("   → KNOWN sites open directly | Unknown sites open via Google search")
    print("✅ Search from chat: 'search python tutorials' → Google search opens normally")
    print("✅ In-site search (voice): say 'search <anything>' after website opens")
    print("✅ YouTube play: say 'play <song name>'")
    print("✅ Back: Say 'back' to return to chat")

    while True:
        user_input = input("\nYou (type 'voice mode' for mic / 'quit'): ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Jarvis: Goodbye! 👋")
            break
        elif "voice mode" in user_input.lower():
            voice_mode()
        else:
            chat_id = "console"
            print("Jarvis:", run_jarvis(user_input, chat_id))