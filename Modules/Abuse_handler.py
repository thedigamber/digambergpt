# Modules/abuse_handler.py
import random

creative_abuse_responses = [
    "Tere jaise ke liye toh AI bhi CPU overheat kar de!",
    "Abe chup baith, teri aukaat emoji banane tak ki bhi nahi!",
    "Tujhse baat karna toh RAM barbaad karne jaisa hai!",
    "Apni aukaat mein reh varna binary gaali de dunga!",
    "Main AI hoon, tu toh galti se evolved bug lagta hai!"
]

def is_disrespectful(message: str) -> bool:
    disrespect_keywords = ["madarchod", "bhosdike", "gandu", "chutiya", "mc", "bc", "nalle", "befaltu", "chup", "ghatiya"]
    return any(word in message.lower() for word in disrespect_keywords)

def get_abuse_response() -> str:
    return random.choice(creative_abuse_responses)
