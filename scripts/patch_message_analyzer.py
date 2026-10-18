with open("apps/api/src/engines/message_analyzer.py", "r", encoding="utf-8") as f:
    code = f.read()

target_block = '''    @classmethod
    def _deobfuscate_text(cls, text: str) -> str:
        """Deobfuscates adversarial evasions: zero-width spaces, leetspeak, homoglyphs, and emojis."""
        if not text:
            return ""
        # 1. Strip zero-width characters and soft hyphens
        cleaned = re.sub(r"[\\u200b\\u200c\\u200d\\ufeff\\u00ad\\u2060\\u200e\\u200f]", "", text)
        
        # 2. De-space spaced letters: 'g u a r a n t e e d' -> 'guaranteed'
        cleaned = re.sub(r"\\b[a-zA-Z](?: [a-zA-Z]){2,}\\b", lambda m: m.group(0).replace(" ", ""), cleaned)
        
        # 3. Transliterate Cyrillic homoglyphs
        homoglyphs = {
            "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "ѕ": "s", "і": "i", "ј": "j",
            "у": "y", "х": "x", "А": "A", "В": "B", "Е": "E", "О": "O", "Р": "P", "С": "C",
            "Т": "T", "Н": "H", "М": "M",
        }
        for cyr, lat in homoglyphs.items():
            cleaned = cleaned.replace(cyr, lat)
            
        # 4. Leetspeak translation
        leet_map = {
            "@": "a", "0": "o", "1": "i", "3": "e", "7": "t", "5": "s", "$": "s", "!": "i",
        }
        # Translate leetspeak only within token words
        tokens = cleaned.split()
        translated_tokens = []
        for tok in tokens:
            # If token has alphanumeric plus leet symbols, substitute
            if any(c in leet_map for c in tok) and any(c.isalnum() for c in tok):
                for lk, lv in leet_map.items():
                    tok = tok.replace(lk, lv)
            translated_tokens.append(tok)
        cleaned_leet = " ".join(translated_tokens)
        
        # 5. Remove disruptive emoji insertions between word characters
        cleaned_emoji = re.sub(r"([a-zA-Z0-9])[\\U00010000-\\U0010ffff\\u2600-\\u27bf\\s]+([a-zA-Z0-9])", r"\\1\\2", cleaned_leet)
        return cleaned_emoji'''

replacement_block = '''    @classmethod
    def _deobfuscate_text(cls, text: str) -> str:
        """Deobfuscates adversarial evasions: zero-width spaces, leetspeak, homoglyphs, and emojis."""
        if not text:
            return ""
        # 1. Strip zero-width characters and soft hyphens
        cleaned = re.sub(r"[\\u200b\\u200c\\u200d\\ufeff\\u00ad\\u2060\\u200e\\u200f]", "", text)
        
        # 2. Transliterate Cyrillic homoglyphs
        homoglyphs = {
            "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "ѕ": "s", "і": "i", "ј": "j",
            "у": "y", "х": "x", "А": "A", "В": "B", "Е": "E", "О": "O", "Р": "P", "С": "C",
            "Т": "T", "Н": "H", "М": "M",
        }
        for cyr, lat in homoglyphs.items():
            cleaned = cleaned.replace(cyr, lat)
            
        # 3. De-space spaced letters only for sequences of 3+ single characters: 'g u a r a n t e e d' -> 'guaranteed'
        cleaned = re.sub(r"\\b[a-zA-Z](?: [a-zA-Z]){2,}\\b", lambda m: m.group(0).replace(" ", ""), cleaned)
        
        # 4. Remove disruptive emoji characters
        cleaned = re.sub(r"[\\U00010000-\\U0010ffff\\u2600-\\u27bf\\u2300-\\u23ff]", "", cleaned)
        
        # 5. Leetspeak translation on words containing alpha chars
        leet_map = {
            "@": "a", "0": "o", "1": "i", "3": "e", "7": "t", "5": "s", "$": "s", "!": "i",
        }
        tokens = cleaned.split()
        translated_tokens = []
        for tok in tokens:
            if any(c.isalpha() for c in tok) and any(c in leet_map for c in tok):
                for lk, lv in leet_map.items():
                    tok = tok.replace(lk, lv)
            translated_tokens.append(tok)
        return " ".join(translated_tokens)'''

if target_block in code:
    code = code.replace(target_block, replacement_block)
    with open("apps/api/src/engines/message_analyzer.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("Replaced _deobfuscate_text successfully.")
else:
    print("Error: target_block not found in code.")
