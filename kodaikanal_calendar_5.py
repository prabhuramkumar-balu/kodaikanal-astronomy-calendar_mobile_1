import streamlit as st
from datetime import datetime, date
from calendar import monthcalendar, setfirstweekday, MONDAY
import pytz
from astral.sun import sun
from astral import LocationInfo
import ephem
import pandas as pd

# --- Setup ---
setfirstweekday(MONDAY)
IST = pytz.timezone("Asia/Kolkata")
location = LocationInfo("Kodaikanal", "India", "Asia/Kolkata", 10.2306, 77.4686)

st.set_page_config(page_title="Kodaikanal Astronomy Calendar", layout="centered")
st.title("📅 Kodaikanal Astronomy Calendar")
st.caption("Sunrise, Sunset, Moon Phase, Moonrise/Set, Planetary Rise/Set & Zenith Times (IST, 12-hour format)")

now_ist = datetime.now(IST)

# Session state for selected date
if "selected_date" not in st.session_state:
    st.session_state.selected_date = now_ist.date()

# Year/month selection
year = st.number_input("Select Year", min_value=1900, max_value=2100, value=now_ist.year)
months = ["January","February","March","April","May","June","July","August","September","October","November","December"]
month_name = st.selectbox("Select Month", months, index=now_ist.month-1)
month_num = months.index(month_name) + 1
cal = monthcalendar(year, month_num)

today = now_ist.date()
weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Inject CSS to make calendar horizontally scrollable on small screens
st.markdown(
    """
    <style>
    .calendar-wrapper {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        border: 1px solid #ddd;
        padding: 8px;
        border-radius: 8px;
        max-width: 100%;
    }
    .calendar-day-button button {
        min-width: 32px;
        max-width: 40px;
        padding: 4px;
        font-size: 0.9rem;
        margin: 2px 0;
    }
    .calendar-header {
        font-weight: bold;
        text-align: center;
        width: 40px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("### 📅 Calendar (Tap on a day to select)")

# Container div for horizontal scroll on mobile
st.markdown('<div class="calendar-wrapper">', unsafe_allow_html=True)

# Weekday headers row
cols = st.columns(7)
for i, wd in enumerate(weekday_labels):
    cols[i].markdown(f'<div class="calendar-header">{wd}</div>', unsafe_allow_html=True)

# Calendar days rows
for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].markdown(" ")
        else:
            dt = date(year, month_num, day)
            label = str(day)
            # Emoji highlights for today and selected day
            if dt == today:
                label = f"🟠 {day}"
            if dt == st.session_state.selected_date:
                label = f"🔵 {day}"
            # Use button with a unique key
            if cols[i].button(label, key=f"day-{year}-{month_num}-{day}"):
                st.session_state.selected_date = dt

st.markdown("</div>", unsafe_allow_html=True)

# Continue with astronomy calculations as before...
sel = st.session_state.selected_date
st.markdown("---")
st.header(f"🌠 Astronomy Data for {sel.strftime('%A, %d %B %Y')}")

def to_ist(dt):
    return dt.astimezone(IST).strftime("%I:%M %p") if dt else "N/A"

sun_times = sun(location.observer, date=sel, tzinfo=IST)
sunrise, sunset, solar_noon = [sun_times[k].strftime("%I:%M %p") for k in ("sunrise", "sunset", "noon")]

observer = ephem.Observer()
observer.lat, observer.lon = str(location.latitude), str(location.longitude)
observer.date = datetime(sel.year, sel.month, sel.day).strftime('%Y/%m/%d')

def moon_phase_name(phase):
    if phase < 1:
        return "New Moon"
    elif phase < 49:
        return "Waxing Crescent"
    elif phase < 51:
        return "First Quarter"
    elif phase < 99:
        return "Waxing Gibbous"
    elif phase <= 100:
        return "Full Moon"
    elif phase > 99:
        return "Waning Gibbous"
    elif phase > 51:
        return "Last Quarter"
    else:
        return "Waning Crescent"

def get_times(body):
    observer.date = datetime(sel.year, sel.month, sel.day)
    try:
        rise = observer.next_rising(body).datetime().astimezone(IST)
    except:
        rise = None
    try:
        set_ = observer.next_setting(body).datetime().astimezone(IST)
    except:
        set_ = None
    try:
        zen = observer.next_transit(body).datetime().astimezone(IST)
    except:
        zen = None
    return to_ist(rise), to_ist(set_), to_ist(zen)

moon = ephem.Moon(observer)
moon_phase_txt = f"{moon.phase:.1f}% ({moon_phase_name(moon.phase)})"
moon_rise, moon_set, moon_zen = get_times(moon)

planets = {
    "Mercury": ephem.Mercury(),
    "Venus": ephem.Venus(),
    "Mars": ephem.Mars(),
    "Jupiter": ephem.Jupiter(),
    "Saturn": ephem.Saturn()
}

planet_times = {}
for name, body in planets.items():
    planet_times[name] = get_times(body)

with st.expander("🌅 Sun"):
    st.write(f"**Sunrise:** {sunrise}")
    st.write(f"**Solar Noon (Zenith):** {solar_noon}")
    st.write(f"**Sunset:** {sunset}")

with st.expander("🌕 Moon"):
    st.write(f"**Illumination:** {moon_phase_txt}")
    st.write(f"**Moonrise:** {moon_rise}")
    st.write(f"**Moonset:** {moon_set}")
    st.write(f"**Moon Zenith:** {moon_zen}")

planet_df = pd.DataFrame.from_dict(
    planet_times,
    orient="index",
    columns=["Rise (IST)", "Set (IST)", "Zenith (IST)"]
)

with st.expander("🪐 Planetary Rise/Set & Zenith Times"):
    st.dataframe(planet_df, use_container_width=True)
