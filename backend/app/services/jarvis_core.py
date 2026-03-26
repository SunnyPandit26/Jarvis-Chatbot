import datetime
import requests
import re
import random
from quote import quote
import datetime
import holidays
import urllib.parse
import math
from deep_translator import GoogleTranslator



API_KEY = "39a77652adf7043638f153373616a4f4"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

NEWS_API_KEY = "1a4d4aa72bd2499b89b7fe2469f96059"  # Replace with your NewsAPI key
NEWS_BASE_URL = "https://newsapi.org/v2/top-headlines"






# ---------------- GREETING ----------------

def get_greeting():
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"


def handle_greeting(query):
    query = query.lower()

    if query.strip() in ["hello", "hi", "hey", "jarvis"]:
        greeting = get_greeting()
        return f"{greeting}! How can I assist you?"

    return None


# # ---------------- WEATHER ----------------

# def get_weather(city):
#     try:
#         url = f"{BASE_URL}?q={city}&appid={API_KEY}&units=metric"
#         response = requests.get(url)
#         data = response.json()

#         if data.get("cod") != 200:
#             return f"Sorry, couldn't fetch weather for {city}."

#         main = data["main"]
#         weather = data["weather"][0]["description"]
#         temp = main["temp"]
#         feels_like = main["feels_like"]
#         humidity = main["humidity"]
#         wind_speed = data["wind"]["speed"]

#         return (f"Weather in {city}: {weather}. "
#                 f"Temperature is {temp}°C, feels like {feels_like}°C. "
#                 f"Humidity is {humidity}%. "
#                 f"Wind speed is {wind_speed} m/s.")

#     except Exception:
#         return "There was a problem getting the weather."


# def handle_weather(query):

#     lemmas = [token.lemma_ for token in doc]

#     weather_words = ["weather", "temperature", "rain", "forecast"]

#     if any(word in lemmas for word in weather_words):

#         # extract city (named entity)
#         for ent in doc.ents:
#             if ent.label_ == "GPE":  # location
#                 return get_weather(ent.text)

#         return get_weather("delhi")

#     return None


# ---------------- quote----------------


def get_random_quote():
    try:
        response = requests.get("https://zenquotes.io/api/random")
        data = response.json()

        # FIX: access first item in list
        quote_data = data[0]

        text = quote_data["q"]
        author = quote_data["a"]

        return f'💡 "{text}" — {author}'

    except Exception as e:
        return "Sorry, couldn't fetch a quote right now."

def handle_quote(query):
    query = query.lower()

    if any(word in query for word in ["quote", "motivation", "inspire"]):
        return get_random_quote()

    return None

# ---------------- holidays----------------


def get_holidays(country_code="IN", year=None):
    """
    Get all public holidays for the full year using the holidays package.
    Supports many countries like IN, US, UK, CA, AU, FR, DE, etc.
    """

    if not year:
        year = datetime.date.today().year

    try:
        # Load holidays for given country & year
        country_holidays = holidays.CountryHoliday(country_code, years=year)

        if not country_holidays:
            return f"No holidays found for {country_code} in {year}."

        # Sort and show all holidays
        holiday_list = []
        for date, name in sorted(country_holidays.items()):
            holiday_list.append(f"{date}: {name}")

        full_list = "\n".join(holiday_list)

        return f"📅 Holidays in {country_code} ({year}):\n" + full_list

    except Exception as e:
        return f"Error fetching holidays: {e}"
    
    
def handle_holidays(query):
    query = query.lower()

    if "holiday" in query:
        
        # default values
        country = "IN"
        year = datetime.date.today().year

        # detect year (if user says 2025 etc.)
        import re
        match = re.search(r"\b(20\d{2})\b", query)
        if match:
            year = int(match.group(1))

        # detect country (basic)
        if "us" in query or "america" in query:
            country = "US"
        elif "uk" in query:
            country = "GB"
        elif "india" in query:
            country = "IN"

        return get_holidays(country, year)

    return None

# ---------------- Wikipedia Summary ----------------


def get_short_wikipedia_summary(topic, lang="en"):
    headers = {
        "User-Agent": "JarvisBot/1.0"
    }

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

        return f"📘 {title}\n\n{extract}"

    except Exception:
        return "Error fetching Wikipedia data"
    
    
def handle_wikipedia(query):
    query = query.lower()

    if "wikipedia" in query or "who is" in query or "what is" in query:

           # remove trigger words
         topic = query.replace("wikipedia", "")
         topic = topic.replace("who is", "")
         topic = topic.replace("what is", "")
         topic = topic.strip()

         return get_short_wikipedia_summary(topic)

    return None


# ---------------- news ----------------

def get_news(query=None, country="in", category=None):
    """
    Fetch latest headlines from NewsAPI.org.
    Works for country, category, or keyword searches.
    """
    try:
        base_url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": NEWS_API_KEY,
            "country": country,
            "pageSize": 5,
            "language": "en"
        }

        # Add optional filters
        if category:
            params["category"] = category
        if query:
            # Avoid using overly generic keywords like "news" or "headlines"
            query = query.strip().lower()
            if query not in ["news", "headlines"]:
                params["q"] = query

        response = requests.get(base_url, params=params)
        data = response.json()

        # Check for API-level issues
        if data.get("status") != "ok":
            return f"⚠️ Error fetching news: {data.get('message', 'Unknown error')}"

        articles = data.get("articles", [])
        if not articles:
            return "Sorry, no recent news found."

        headlines = []
        for i, article in enumerate(articles[:5], start=1):
            title = article.get("title", "No title")
            source = article.get("source", {}).get("name", "Unknown Source")
            headlines.append(f"{i}. {title} ({source})")

        news_summary = "📰 Here are the top headlines:\n" + "\n".join(headlines)
        return news_summary

    except Exception as e:
        return f"There was a problem getting the news: {e}"
    

def handle_news(query):
    query = query.lower()

    if "news" in query or "headlines" in query:

        # detect category (basic)
        if "sports" in query:
            return get_news(category="sports")
        elif "business" in query:
            return get_news(category="business")
        elif "technology" in query:
            return get_news(category="technology")
        elif "health" in query:
            return get_news(category="health")

        # detect keyword search
        words = query.replace("news", "").strip()
        if words:
            return get_news(query=words)

        # default
        return get_news()

    return None

# ---------------- movies ----------------

def get_movie_info(movie_name):
    try:
        api_key = "3e5458a"  # replace with your valid OMDb API key
        url = f"http://www.omdbapi.com/?t={urllib.parse.quote(movie_name)}&apikey={api_key}"
        response = requests.get(url)
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

        return (f"🎬 **{title}** ({year})\n"
                f"🎭 Genre: {genre}\n"
                f"⭐ IMDb Rating: {imdb_rating}\n"
                f"🎥 Director: {director}\n"
                f"👥 Cast: {actors}\n"
                f"📖 Plot: {plot}")
    except Exception as e:
        return f"Error fetching movie info: {e}"

def handle_movie(query):
    query = query.lower()

    if "movie" in query or "film" in query:

        import re
        match = re.search(r"(movie|film)\s+(.*)", query)

        if match:
            movie = match.group(2).strip()
        else:
            return "Please tell me the movie name."

        return get_movie_info(movie)

    return None

# ---------------- quiz ----------------


quiz_questions = {
    "What is the capital of France?": "paris",
    "How many legs does a spider have?": "8",
    "What planet is known as the red planet?": "mars",
    "What is 5 multiplied by 6?": "30"
}

quiz_state = {
    "active": False,
    "question": None,
    "answer": None,
    "awaiting_continue": False
}


def get_random_question():
    q, a = random.choice(list(quiz_questions.items()))
    return q, a


def handle_quiz(query):
    global quiz_state
    query = query.lower().strip()

    # START QUIZ
    if "quiz" in query and not quiz_state["active"]:
        q, a = get_random_question()
        quiz_state.update({
            "active": True,
            "question": q,
            "answer": a,
            "awaiting_continue": False
        })
        return f"🎯 Quiz Time!\n\n{q}"

    # IF QUIZ ACTIVE
    if quiz_state["active"]:

        # CHECK ANSWER
        if not quiz_state["awaiting_continue"]:
            if query == quiz_state["answer"]:
                response = "✅ Correct!"
            else:
                response = f"❌ Wrong! Correct answer was {quiz_state['answer']}"

            quiz_state["awaiting_continue"] = True
            return response + "\n\nDo you want another question? (yes/no)"

        # HANDLE CONTINUE
        else:
            if query in ["yes", "y"]:
                q, a = get_random_question()
                quiz_state.update({
                    "question": q,
                    "answer": a,
                    "awaiting_continue": False
                })
                return f"🎯 Next Question:\n\n{q}"

            elif query in ["no", "n"]:
                quiz_state = {
                    "active": False,
                    "question": None,
                    "answer": None,
                    "awaiting_continue": False
                }
                return "👍 Okay! See you next time for quiz."

            else:
                return "Please answer with yes or no."

    return None

# ---------------- GUESS THE NUMBER ----------------

guess_state = {
    "active": False,
    "number": None,
    "attempts": 0,
    "max_attempts": 5,
    "awaiting_continue": False
}


def handle_guess_number(query):
    global guess_state
    query = query.lower().strip()

    # START GAME
    if "guess" in query and "number" in query and not guess_state["active"]:
        guess_state = {
            "active": True,
            "number": random.randint(1, 50),
            "attempts": 0,
            "max_attempts": 5,
            "awaiting_continue": False
        }
        return "🎯 I have chosen a number between 1 and 50. Try to guess it! You have 5 chances"

    # IF GAME ACTIVE
    if guess_state["active"]:

        # HANDLE CONTINUE
        if guess_state["awaiting_continue"]:
            if query in ["yes", "y"]:
                guess_state = {
                    "active": True,
                    "number": random.randint(1, 50),
                    "attempts": 0,
                    "max_attempts": 5,
                    "awaiting_continue": False
                }
                return "🎯 New game started! Guess the number (1–50)."

            elif query in ["no", "n"]:
                guess_state["active"] = False
                return "👍 Okay! See you next time."

            else:
                return "Please answer with yes or no."

        # HANDLE GUESS
        try:
            guess = int(query)
        except:
            return "Please enter a valid number."

        guess_state["attempts"] += 1

        if guess == guess_state["number"]:
            guess_state["awaiting_continue"] = True
            return "🎉 Correct! You guessed it right!\n\nPlay again? (yes/no)"

        elif guess < guess_state["number"]:
            msg = "Too low!"
        else:
            msg = "Too high!"

        # CHECK ATTEMPTS
        if guess_state["attempts"] >= guess_state["max_attempts"]:
            num = guess_state["number"]
            guess_state["awaiting_continue"] = True
            return f"❌ Game over! The number was {num}.\n\nPlay again? (yes/no)"

        return msg
    
    return None

# ---------------- CALCULATOR ----------------

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
        return "Sorry, I couldn’t calculate that."
    
def handle_calculator(query):
    query = query.lower()

    if any(word in query for word in ["calculate", "+", "-", "*", "/", "multiply", "divide", "plus"]):
        
        # remove trigger word
        expression = query.replace("calculate", "").strip()

        return calculate_expression(expression)

    return None

# ---------------- ai fallback ----------------
def handle_ai(query):
    return "Sorry, I don't understand that yet. I'm still learning new things every day!"

# ---------------- translation ----------------


def translate_text(text, target_language="hi"):
    try:
        translated = GoogleTranslator(
            source='auto',
            target=target_language
        ).translate(text)

        return translated

    except Exception:
        return "Error in translation"
    
    
def handle_translate(query):
    query = query.lower()

    if "translate" in query:

        # basic extraction
        text = query.replace("translate", "").strip()

        if not text:
            return "What do you want me to translate?"

        translated = translate_text(text)

        return f"🌐 Translation:\n{translated}"

    return None


# ---------------- MAIN BRAIN ----------------
 
def run_jarvis(query):

    # Games
    response = handle_quiz(query)
    if response:
        return response

    response = handle_guess_number(query)
    if response:
        return response

    # # APIs
    # response = handle_weather(query)
    # if response:
    #     return response

    response = handle_news(query)
    if response:
        return response

    response = handle_movie(query)
    if response:
        return response

    response = handle_wikipedia(query)
    if response:
        return response

    response = handle_quote(query)
    if response:
        return response

    response = handle_holidays(query)
    if response:
        return response
    
    # Translation
    response = handle_translate(query)
    if response:
     return response

    # Tools
    response = handle_calculator(query)
    if response:
        return response

    # Greeting
    response = handle_greeting(query)
    if response:
        return response

    # 🔥 FINAL FALLBACK → AI
    return handle_ai(query)

