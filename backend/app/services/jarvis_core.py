from dotenv import load_dotenv
import os
import datetime
import requests
import re
import random
import holidays
import urllib.parse
import math
from deep_translator import GoogleTranslator
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HF_TOKEN"],
)


# ---------------- RESPONSE CLEANUP ----------------
def clean_ai_response(text):
    if not text:
        return "Sorry, I could not generate a proper response."

    text = text.strip()

    replacements = {
        "Srry": "Sorry",
        "srry": "Sorry",
        "Iam": "I am",
        "im": "I'm",
        "i'm": "I'm",
        "i": "I",
        "iunderstand": "I understand",
        "idont": "I don't",
        "cant": "can't",
        "dont": "don't",
        "doesnt": "doesn't",
        "wont": "won't",
        "couldnt": "couldn't",
        "shouldnt": "shouldn't",
        "wouldnt": "wouldn't"
    }

    for old, new in replacements.items():
        text = re.sub(rf"\b{re.escape(old)}\b", new, text)

    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'([a-z])([A-Z][a-z])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)

    text = re.sub(r'\biunderstand\b', "I understand", text, flags=re.IGNORECASE)
    text = re.sub(r'\biapologize\b', "I apologize", text, flags=re.IGNORECASE)
    text = re.sub(r'\bletme\b', "let me", text, flags=re.IGNORECASE)
    text = re.sub(r'\bheres\b', "Here's", text, flags=re.IGNORECASE)
    text = re.sub(r'\bthats\b', "That's", text, flags=re.IGNORECASE)

    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', '\n', text)

    if text and text[0].islower():
        text = text[0].upper() + text[1:]

    return text.strip()


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
    query = query.lower().strip()
    if query in ["hello", "hi", "hey", "jarvis"]:
        greeting = get_greeting()
        return f"{greeting}! How can I assist you?"
    return None


# ---------------- QUOTE ----------------
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


# ---------------- HOLIDAYS ----------------
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


# ---------------- WIKIPEDIA ----------------
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
        return f"📘 {title}\n\n{extract}"
    except Exception:
        return "Error fetching Wikipedia data"


def handle_wikipedia(query):
    query = query.lower()
    if "wikipedia" in query or "who is" in query or "what is" in query:
        topic = query.replace("wikipedia", "").replace("who is", "").replace("what is", "").strip()
        if topic:
            return get_short_wikipedia_summary(topic)
    return None


# ---------------- MOVIES ----------------
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


# ---------------- QUIZ ----------------
quiz_questions = {
    "What is the capital of France?": "paris",
    "How many legs does a spider have?": "8",
    "What planet is known as the red planet?": "mars",
    "What is 5 multiplied by 6?": "30"
}
quiz_state = {"active": False, "question": None, "answer": None, "awaiting_continue": False}


def get_random_question():
    q, a = random.choice(list(quiz_questions.items()))
    return q, a


def handle_quiz(query):
    global quiz_state
    query = query.lower().strip()
    if "quiz" in query and not quiz_state["active"]:
        q, a = get_random_question()
        quiz_state.update({"active": True, "question": q, "answer": a, "awaiting_continue": False})
        return f"🎯 Quiz Time!\n\n{q}"
    if quiz_state["active"]:
        if not quiz_state["awaiting_continue"]:
            if query == quiz_state["answer"]:
                response = "✅ Correct!"
            else:
                response = f"❌ Wrong! Correct answer was {quiz_state['answer']}"
            quiz_state["awaiting_continue"] = True
            return response + "\n\nDo you want another question? (yes/no)"
        else:
            if query in ["yes", "y"]:
                q, a = get_random_question()
                quiz_state.update({"question": q, "answer": a, "awaiting_continue": False})
                return f"🎯 Next Question:\n\n{q}"
            elif query in ["no", "n"]:
                quiz_state = {"active": False, "question": None, "answer": None, "awaiting_continue": False}
                return "👍 Okay! See you next time for quiz."
            else:
                return "Please answer with yes or no."
    return None


# ---------------- GUESS THE NUMBER ----------------
guess_state = {"active": False, "number": None, "attempts": 0, "max_attempts": 5, "awaiting_continue": False}


def handle_guess_number(query):
    global guess_state
    query = query.lower().strip()
    if "guess" in query and "number" in query and not guess_state["active"]:
        guess_state = {
            "active": True,
            "number": random.randint(1, 50),
            "attempts": 0,
            "max_attempts": 5,
            "awaiting_continue": False
        }
        return "🎯 I have chosen a number between 1 and 50. Try to guess it! You have 5 chances"
    if guess_state["active"]:
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
        try:
            guess = int(query)
        except Exception:
            return "Please enter a valid number."
        guess_state["attempts"] += 1
        if guess == guess_state["number"]:
            guess_state["awaiting_continue"] = True
            return "🎉 Correct! You guessed it right!\n\nPlay again? (yes/no)"
        elif guess < guess_state["number"]:
            msg = "Too low!"
        else:
            msg = "Too high!"
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
        return "Sorry, I couldn't calculate that."


def handle_calculator(query):
    query = query.lower()
    if any(word in query for word in ["calculate", "+", "-", "*", "/", "multiply", "divide", "plus"]):
        expression = query.replace("calculate", "").strip()
        return calculate_expression(expression)
    return None


# ---------------- TRANSLATION ----------------
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


# ---------------- HUGGING FACE AI FALLBACK ----------------
def handle_huggingface_ai(query):
    try:
        system_prompt = (
            "You are Jarvis, a helpful AI assistant. "
            "Always reply in clear English with proper spacing and grammar. "
            "Never write words like 'Srry'; always write 'Sorry'. "
            "If the user asks for code, provide complete working code inside proper code blocks. "
            "Do not unnecessarily shorten answers. "
            "Give detailed, practical, and direct answers. "
            "If the task is programming-related, explain briefly and then provide code."
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
        return "Sorry, the AI is unavailable right now. Please try again later."


# ---------------- MAIN BRAIN ----------------
def run_jarvis(query):
    response = handle_quiz(query)
    if response:
        return response

    response = handle_guess_number(query)
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

    response = handle_translate(query)
    if response:
        return response

    response = handle_calculator(query)
    if response:
        return response

    response = handle_greeting(query)
    if response:
        return response

    return handle_huggingface_ai(query)


if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Jarvis: Goodbye! 👋")
            break
        print("Jarvis:", run_jarvis(user_input))