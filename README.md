# Singhacks

-- Scope --
Only MAS

-- Plan --
1.1. Grok_A webscrapes MAS -> JSON (Low)
    UI - create new versions with delta (what changed) and high-impact fields (High)
1.2. for each JSON guidance (no huge detail), prompt t2t Groq on whether violated
1.2.b. also put all features into one neural network for Low-Medium-High risk inference
1.3. Grok_C combines 1.2 to generate next steps together with priority status
    UI - need to have transaction history

2. we can vibecode this agent its just image-to-text