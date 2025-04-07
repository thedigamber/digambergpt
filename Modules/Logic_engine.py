# Modules/logic_engine.py

def internal_ai_logic(prompt: str) -> str:
    if "your name" in prompt.lower():
        return "Mera naam DigamberGPT hai, tera dard ka solution!"
    elif "kya kar sakte ho" in prompt.lower():
        return "Main sab kuch kar sakta hoon — chat, image, roast, gaali, sab!"
    else:
        return f"Tune bola: '{prompt}' — aur main sochta hoon: tu genius hai ya mirage?"
