#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
🎂 Birthday Surprise: Streamlit version
---------------------------------------
Reads your WhatsApp chat (chat.txt) and shows a tap-through birthday story.

1. Put this file, chat.txt and your photos in the same folder
2. Install the tools (once):   pip install -U streamlit pillow
3. Run:                        streamlit run streamlit_app.py
4. Your browser opens the app (or go to http://localhost:8501)

No chat.txt in the folder? The app lets you upload it instead.
Your chat is only read on your own computer. The pages show counts, top words and photos,
never your actual messages.
"""

import base64, io, os, re
from collections import Counter
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

# ============ YOUR SETTINGS ============
HER_NAME = "Kirthi"          # her name in the chat
YOUR_NAME = "Hari"
NICKNAME = "Amigaa"          # shown in the big heading
YEARS = 13
HIGHLIGHT = "buddy"          # the word shown big in the middle of the word cloud
BIRTHDAY_MESSAGE = ("Thank you for every time you pay attention for me, every silly joke and every time you "
                    "showed up for me. Happy Birthday to my best friend ever! 💖")
JOKE_SETUP = ("A man and a woman are travelling in a train. She says: “Every time you smile, "
              "I feel like inviting you to my place.” He says: “Awwww! Why?”")
JOKE_PUNCHLINE = "She says: “I’m a dentist.” 😁"
CHAT_FILE = "chat.txt"
PHOTOS = [ "photo4.png", "photo3.png", "photo5.png"]
CARD_PHOTO = "photo5.png"    # photo on the first screen
# =======================================

PINK, PURPLE, LILAC = "#d6336c", "#7048e8", "#b197fc"
HERE = os.path.dirname(os.path.abspath(__file__))
def path(name): return os.path.join(HERE, name)

LINE = re.compile(r"^\[?(\d{1,2})/(\d{1,2})/(\d{2,4}),?\s+(\d{1,2}):(\d{2})(?::\d{2})?\s?([apAP][mM])?\]?\s*-?\s*([^:]+?):\s(.*)$")
EMOJI = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
STOP = set("""the and for with you are was this that not have has had its dont just what when how why who her his she
they them from all get got lol haha media omitted message deleted null yes okay hai haan nahi kya kar toh bhi""".split())

st.set_page_config(page_title="Happy Birthday!", page_icon="🎂", layout="centered")
st.markdown(f"""<style>
.stApp {{ background: linear-gradient(160deg,#ffe3ec,#e6e0ff); }}
.stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label {{ color:#3a2b4d; font-family:Georgia,serif; }}
.stApp span:not([data-testid="stIconMaterial"]) {{ color:#3a2b4d; }}
[data-testid="stIconMaterial"] {{ font-family:"Material Symbols Rounded" !important; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ background:#fff; border-radius:24px; box-shadow:0 10px 30px #0002; }}
.big {{ font-size:3.4rem; font-weight:bold; color:{PINK} !important; text-align:center; line-height:1.1; }}
.mid {{ text-align:center; }}
.avatar {{ width:150px; height:150px; border-radius:50%; object-fit:cover; border:6px solid #fff; box-shadow:0 8px 22px #0003; }}
.badge {{ display:inline-block; background:#ffe3ec; color:{PINK} !important; border-radius:999px; padding:6px 16px; font-weight:bold; }}
.cloud {{ text-align:center; line-height:1.5; }}
.cloud span {{ display:inline-block; margin:2px 7px; }}
.hl {{ text-align:center; font-size:4rem; font-weight:bold; color:{PINK} !important; margin:4px 0; }}
.msg {{ font-size:1.25rem; font-style:italic; line-height:1.6; text-align:center; }}
</style>""", unsafe_allow_html=True)


# ---------- reading the chat ----------
@st.cache_data(show_spinner="Reading your chat…")
def build_stats(text: str):
    raw = []
    for line in text.splitlines():
        line = line.replace("\u200e", "").replace("\u202f", " ")
        m = LINE.match(line)
        if m:
            raw.append({"a": int(m[1]), "b": int(m[2]), "y": int(m[3]), "h": int(m[4]),
                        "ap": m[6], "who": m[7].strip(), "text": m[8]})
        elif raw:                                       # a multi-line message continues here
            raw[-1]["text"] += " " + line
    if not raw:
        return None

    month_first = any(r["b"] > 12 for r in raw) and not any(r["a"] > 12 for r in raw)
    you_present = any(r["who"] == "You" for r in raw)
    msgs = []
    for r in raw:
        hour = r["h"]
        if r["ap"]:
            hour = hour % 12 + (12 if r["ap"].lower() == "pm" else 0)
        year = r["y"] if r["y"] > 99 else r["y"] + 2000
        day, month = (r["b"], r["a"]) if month_first else (r["a"], r["b"])
        try:
            date = datetime(year, month, day)
        except ValueError:
            continue
        who = r["who"]
        if you_present:                                  # "You" -> your name, her number -> her name
            who = YOUR_NAME if who == "You" else HER_NAME
        msgs.append((date, hour, who, r["text"]))

    people, hours = Counter(m[2] for m in msgs), Counter(m[1] for m in msgs)
    days = Counter(m[0].date() for m in msgs)
    words, emojis = Counter(), Counter()
    for _, _, _, t in msgs:
        if "omitted" in t.lower():
            continue
        emojis.update(EMOJI.findall(t))
        for w in re.findall(r"[a-z']{3,}", t.lower()):
            if w not in STOP:
                words[w] += 1
    first, last = msgs[0][0], msgs[-1][0]
    best_day, best_count = days.most_common(1)[0]
    return {
        "total": len(msgs), "span": (last - first).days, "first": first,
        "people": people.most_common(2),
        "words": [(w, c) for w, c in words.most_common(40) if w != HIGHLIGHT.lower()][:28],
        "emojis": emojis.most_common(6),
        "hours": [hours.get(h, 0) for h in range(24)],
        "night": sum(hours.get(h, 0) for h in (23, 0, 1, 2, 3, 4)),
        "peak": max(range(24), key=lambda h: hours.get(h, 0)),
        "best_day": best_day, "best_count": best_count,
    }


def hl(h): return f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"

def photo(name, size=700):
    p = path(name)
    return ImageOps.fit(Image.open(p).convert("RGB"), (size, size)) if os.path.exists(p) else None

def avatar_html(name):
    img = photo(name, 400)
    if img is None:
        return ""
    buf = io.BytesIO(); img.save(buf, "JPEG", quality=85)
    return f'<img class="avatar" src="data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}">'


# ---------- the screens ----------
def screen_intro(D):
    st.markdown(f"""<div class="mid">{avatar_html(CARD_PHOTO) or avatar_html(PHOTOS[0] if PHOTOS else "")}
        <h1>🎂 Happy Birthday,<br>{NICKNAME}! 🎂</h1>
        <p><span class="badge">{YEARS} years of friendship</span></p>
        <p>I turned our friendship into data.<br>Tap <b>Next</b> 👉</p></div>""", unsafe_allow_html=True)

def screen_messages(D):
    st.subheader("Messages we’ve shared")
    st.markdown(f'<div class="big">{D["total"]:,}</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="mid">over {D["span"]:,} days, since {D["first"]:%d %B %Y}</p>', unsafe_allow_html=True)
    df = pd.DataFrame(D["people"], columns=["who", "messages"])
    st.altair_chart(alt.Chart(df).mark_bar(color=PINK, cornerRadiusEnd=6).encode(
        y=alt.Y("who:N", sort="-x", title=None), x=alt.X("messages:Q", title=None),
        tooltip=["who", "messages"]).properties(height=120), width="stretch")

def screen_words(D):
    st.subheader("The words that are “us”")
    mx = D["words"][0][1]
    half = (len(D["words"]) + 1) // 2
    def cloud(ws):
        colors = [PURPLE, PINK, "#339af0"]
        return '<div class="cloud">' + " ".join(
            f'<span style="font-size:{15 + 26 * c / mx:.0f}px;color:{colors[i % 3]}">{w}</span>'
            for i, (w, c) in enumerate(ws)) + "</div>"
    st.markdown(cloud(D["words"][:half]) + f'<div class="hl">{HIGHLIGHT.upper()}</div>' + cloud(D["words"][half:]),
                unsafe_allow_html=True)
    pick = st.selectbox("Pick a word to see how often we used it", [w for w, _ in D["words"]])
    st.info(f"“{pick}” showed up **{dict(D['words'])[pick]:,}** times")

def screen_emojis(D):
    st.subheader("Our top emojis")
    cols = st.columns(len(D["emojis"]))
    for col, (e, c) in zip(cols, D["emojis"]):
        col.markdown(f'<div class="mid" style="font-size:2.4rem">{e}</div><div class="mid">{c:,}</div>',
                     unsafe_allow_html=True)

def screen_hours(D):
    st.subheader("When we talk the most")
    st.markdown(f'<p class="mid">Peak time: <b>{hl(D["peak"])}</b></p>', unsafe_allow_html=True)
    df = pd.DataFrame({"hour": [hl(h) for h in range(24)], "messages": D["hours"],
                       "peak": [h == D["peak"] for h in range(24)]})
    st.altair_chart(alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("hour:N", sort=None, title=None, axis=alt.Axis(labelAngle=-90)),
        y=alt.Y("messages:Q", title=None),
        color=alt.condition(alt.datum.peak, alt.value(PINK), alt.value(LILAC)),
        tooltip=["hour", "messages"]).properties(height=260), width="stretch")
    st.markdown(f'<p class="mid">🦉 <b>{D["night"]:,}</b> messages between 11 PM and 5 AM</p>', unsafe_allow_html=True)

def screen_best_day(D):
    st.subheader("Our biggest chat day")
    st.markdown(f'<div class="big">{D["best_count"]:,}</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="mid">messages on <b>{D["best_day"]:%d %B %Y}</b>.<br>What was going on that day? 😄</p>',
                unsafe_allow_html=True)

def screen_photos(D):
    st.subheader("Our memories 📸")
    imgs = [i for i in (photo(p) for p in PHOTOS) if i is not None]
    if not imgs:
        st.info("Add photos next to this file to see them here.")
        return
    for row in range(0, len(imgs), 3):
        cols = st.columns(3)
        for col, img in zip(cols, imgs[row:row + 3]):
            col.image(img, width="stretch")

def screen_final(D):
    st.subheader(f"A message from {YOUR_NAME} 💌")
    st.markdown(f'<p class="msg">{BIRTHDAY_MESSAGE}</p>', unsafe_allow_html=True)
    with st.expander("😂 Your birthday joke (tap to open)"):
        st.write(JOKE_SETUP)
        if st.checkbox("Tap for the punchline…"):
            st.success(JOKE_PUNCHLINE)
    st.markdown('<h1 class="mid">🎉 Happy Birthday! 🎉</h1>', unsafe_allow_html=True)
    if not st.session_state.get("ballooned"):
        st.balloons()
        st.session_state.ballooned = True

SCREENS = [screen_intro, screen_messages, screen_words, screen_emojis, screen_hours,
           screen_best_day, screen_photos, screen_final]


# ---------- get the chat ----------
if os.path.exists(path(CHAT_FILE)):
    with open(path(CHAT_FILE), encoding="utf-8") as f:
        text = f.read()
else:
    up = st.file_uploader("Upload your WhatsApp chat export (.txt)", type="txt")
    if up is None:
        st.info("No chat.txt found next to this app. Upload it above. It is only read on this computer.")
        st.stop()
    text = up.getvalue().decode("utf-8", errors="ignore")

D = build_stats(text)
if D is None:
    st.error("Couldn’t find any messages. Please use a WhatsApp “Export chat” .txt file.")
    st.stop()


# ---------- navigation ----------
st.session_state.setdefault("step", 0)
last = len(SCREENS) - 1

def go(delta):
    st.session_state.step = max(0, min(last, st.session_state.step + delta))
    if st.session_state.step != last:
        st.session_state.ballooned = False

def replay():
    st.session_state.step = 0
    st.session_state.ballooned = False

step = st.session_state.step
with st.container(border=True):
    SCREENS[step](D)

st.progress((step + 1) / len(SCREENS))
left, _, right = st.columns([1, 1, 1])
left.button("← Back", on_click=go, args=(-1,), disabled=step == 0, width="stretch")
if step < last:
    right.button("Next →", on_click=go, args=(1,), type="primary", width="stretch")
else:
    right.button("↺ Replay", on_click=replay, width="stretch")

