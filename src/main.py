import streamlit as st
import pdfplumber
import os
import requests
from groq import Groq
from dotenv import load_dotenv
import re
import plotly.graph_objects as go
import time
import json
import streamlit.components.v1 as components

# -----------------------------
# CONFIG
# -----------------------------
MAX_FILE_SIZE_MB = 5
MAX_PDF_PAGES = 10

# -----------------------------
# Load API Key
# -----------------------------
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("GROQ_API_KEY not found in .env file")
    st.stop()

client = Groq(api_key=api_key)

# -----------------------------
# UI STYLE
# -----------------------------
st.set_page_config(page_title="Clinix AI", page_icon="🩺", layout="wide")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
    color: white;
}
h1 { text-align: center; }
.risk-box {
    padding: 20px;
    border-radius: 12px;
    font-size: 22px;
    font-weight: bold;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

st.title("🩺 Clinix AI")
st.markdown("### Upload your blood report and receive AI-powered insights")


# -----------------------------
# AUTO DETECT USER CITY VIA IP
# -----------------------------
def get_user_city():
    """Detect user's city from their IP address using ipapi.co."""
    try:
        response = requests.get("https://ipapi.co/json/", timeout=5)
        data = response.json()
        city    = data.get("city")
        region  = data.get("region")
        country = data.get("country_name")
        if city and country:
            return f"{city}, {country}"
        return city or None
    except Exception:
        return None


# Run IP detection once per session and cache the result
if "detected_city" not in st.session_state:
    with st.spinner("📡 Detecting your location..."):
        st.session_state.detected_city = get_user_city() or ""

# Show location input — pre-filled with auto-detected city
col1, col2 = st.columns([4, 1])
with col1:
    location = st.text_input(
        "📍 Your city for clinic recommendations",
        value=st.session_state.detected_city,
        placeholder="Example: Lucknow, Delhi, Mumbai",
        help="Auto-detected from your IP. You can edit this anytime."
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # vertical align
    if st.button("🔄 Re-detect"):
        with st.spinner("Re-detecting..."):
            detected = get_user_city()
            if detected:
                st.session_state.detected_city = detected
                st.success(f"Detected: {detected}")
                st.rerun()
            else:
                st.warning("Could not detect location.")

if st.session_state.detected_city and location == st.session_state.detected_city:
    st.caption(f"📡 Auto-detected location: **{st.session_state.detected_city}**")

uploaded_file = st.file_uploader("Upload Blood Report (PDF only)", type=["pdf"])


# -----------------------------
# VALIDATION
# -----------------------------
def validate_pdf_file(file):
    if not file:
        return False, "No file uploaded."
    if file.type != "application/pdf":
        return False, "Invalid file type."
    if file.size / (1024 * 1024) > MAX_FILE_SIZE_MB:
        return False, "File too large."
    return True, None


def extract_text_from_pdf(file):
    try:
        text = ""
        with pdfplumber.open(file) as pdf:
            if len(pdf.pages) > MAX_PDF_PAGES:
                return None, "PDF exceeds page limit."
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        return text, None
    except Exception as e:
        return None, str(e)


# -----------------------------
# RISK SCORING
# -----------------------------
def calculate_risk_score(risk_level):
    mapping = {
        "LOW": 20,
        "MODERATE": 45,
        "HIGH": 70,
        "CRITICAL": 90
    }
    risk_level = risk_level.strip().upper()
    return mapping.get(risk_level, 20)


def highlight_abnormal(text):
    replacements = {
        r'\bCRITICAL\b': '<span style="color:#ff4d4d;font-weight:bold;">CRITICAL</span>',
        r'\bHIGH\b': '<span style="color:#ff9933;font-weight:bold;">HIGH</span>',
        r'\bMODERATE\b': '<span style="color:#fff176;font-weight:bold;">MODERATE</span>',
        r'\bLOW\b': '<span style="color:#4dff88;font-weight:bold;">LOW</span>',
        r'\bABNORMAL\b': '<span style="color:#fff176;font-weight:bold;">ABNORMAL</span>',
        r'\bABNORMALITIES\b': '<span style="color:#fff176;font-weight:bold;">ABNORMALITIES</span>',
        r'\bNORMAL\b': '<span style="color:#4dff88;font-weight:bold;">NORMAL</span>',
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


# -----------------------------
# GAUGE
# -----------------------------
def show_risk_gauge(score):
    if score <= 25:
        needle_color = "#00FF88"
    elif score <= 50:
        needle_color = "#FFFF00"
    elif score <= 75:
        needle_color = "#FFA500"
    else:
        needle_color = "#FF2E2E"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={'font': {'size': 40, 'color': needle_color}},
        title={'text': "Health Risk Score"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': needle_color, 'thickness': 0.35},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': needle_color,
            'steps': [
                {'range': [0, 25],  'color': "#003300"},
                {'range': [25, 50], 'color': "#444400"},
                {'range': [50, 75], 'color': "#663300"},
                {'range': [75, 100],'color': "#330000"},
            ],
        }
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': needle_color},
        margin=dict(t=40, b=20)
    )

    return fig


# -----------------------------
# MEDICAL COMPARISON
# -----------------------------
def compare_with_normal_ranges(text):
    reference_ranges = {
        "hemoglobin": (13, 17, "g/dL"),
        "wbc":        (4000, 11000, "/µL"),
        "rbc":        (4.5, 5.9, "million/µL"),
        "platelet":   (150000, 450000, "/µL"),
        "glucose":    (70, 99, "mg/dL"),
        "creatinine": (0.7, 1.3, "mg/dL"),
    }

    results = []
    text_lower = text.lower()

    for marker, (low, high, unit) in reference_ranges.items():
        pattern = rf"{marker}[^0-9]*([0-9]+\.?[0-9]*)"
        match = re.search(pattern, text_lower)

        if match:
            value = float(match.group(1))

            if value < low:
                status, color = "LOW", "orange"
            elif value > high:
                status, color = "HIGH", "red"
            else:
                status, color = "NORMAL", "green"

            results.append((marker.capitalize(), value, f"{low}-{high} {unit}", status, color))

    return results


# -----------------------------
# DISEASE DETECTION
# -----------------------------
def detect_disease(abnormal_findings, summary):
    if isinstance(abnormal_findings, list):
        findings_text = " ".join(abnormal_findings).lower()
    else:
        findings_text = str(abnormal_findings).lower()

    summary_text = summary.lower()
    text = findings_text + " " + summary_text

    disease_map = {
        "Cardiac":   ["heart", "cardiac", "chest pain", "hypertension"],
        "Diabetes":  ["glucose", "diabetes", "blood sugar"],
        "Kidney":    ["creatinine", "kidney", "renal"],
        "Liver":     ["liver", "bilirubin", "hepatitis"],
        "Infection": ["infection", "wbc", "fever"],
        "Anemia":    ["hemoglobin", "anemia", "low hb"],
    }

    for disease, keywords in disease_map.items():
        for keyword in keywords:
            if keyword in text:
                return disease

    return "General"


# -----------------------------
# CLINIC QUERY BUILDER
# -----------------------------
def get_clinic_query(disease):
    clinic_map = {
        "Cardiac":   "cardiologist near me",
        "Diabetes":  "diabetologist near me",
        "Kidney":    "nephrologist near me",
        "Liver":     "gastroenterologist near me",
        "Infection": "internal medicine specialist near me",
        "Anemia":    "hematologist near me",
        "General":   "general physician near me",
    }
    return clinic_map.get(disease, "general physician near me")


# -----------------------------
# MAIN EXECUTION
# -----------------------------
if uploaded_file:
    is_valid, error = validate_pdf_file(uploaded_file)
    if not is_valid:
        st.error(error)
        st.stop()

    with st.spinner("Extracting text..."):
        report_text, error = extract_text_from_pdf(uploaded_file)

    if error:
        st.error(error)
        st.stop()

    with st.spinner("Analyzing health report..."):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict medical AI that always returns valid JSON only."
                },
                {
                    "role": "user",
                    "content": f"""
Analyze the following blood report.

Respond ONLY in valid JSON format like this:

{{
  "risk_level": "LOW or MODERATE or HIGH or CRITICAL",
  "summary": "short health summary",
  "abnormal_findings": ["list abnormal findings"],
  "recommendations": ["medical or lifestyle advice"]
}}

Do not include explanations outside JSON.

Blood Report:
{report_text}
"""
                }
            ]
        )

    ai_output = response.choices[0].message.content

    try:
        parsed = json.loads(ai_output)
    except json.JSONDecodeError:
        st.error("AI did not return valid JSON.")
        st.write(ai_output)
        st.stop()

    risk_level       = parsed.get("risk_level", "LOW").upper()
    summary          = parsed.get("summary", "")
    abnormal_findings = parsed.get("abnormal_findings", [])
    recommendations  = parsed.get("recommendations", [])

    risk_score = calculate_risk_score(risk_level)

    # -----------------------------
    # GAUGE ANIMATION
    # -----------------------------
    st.markdown("## 🚦 Health Risk Meter")

    gauge_placeholder = st.empty()

    for i in range(0, 91, 15):
        gauge_placeholder.plotly_chart(
            show_risk_gauge(i),
            use_container_width=True,
            key=f"gauge_up_{i}"
        )
        time.sleep(0.02)

    for i in range(90, risk_score - 1, -5):
        gauge_placeholder.plotly_chart(
            show_risk_gauge(i),
            use_container_width=True,
            key=f"gauge_down_{i}"
        )
        time.sleep(0.02)

    gauge_placeholder.plotly_chart(
        show_risk_gauge(risk_score),
        use_container_width=True,
        key="gauge_final"
    )

    # -----------------------------
    # STRUCTURED OUTPUT DISPLAY
    # -----------------------------
    st.markdown("## 📋 Medical Summary")
    st.write(summary)

    st.markdown("## ⚠️ Abnormal Findings")
    if isinstance(abnormal_findings, list):
        for item in abnormal_findings:
            st.markdown(f"- {item}")
    else:
        st.write(abnormal_findings)

    st.markdown("## 💡 Recommendations")
    if isinstance(recommendations, list):
        for item in recommendations:
            st.markdown(f"- {item}")
    else:
        st.write(recommendations)

    # -----------------------------
    # MEDICAL COMPARISON
    # -----------------------------
    comparison_results = compare_with_normal_ranges(report_text)

    if comparison_results:
        st.markdown("## 🧪 Medical Comparison With Normal Ranges")

        for marker, value, normal_range, status, color in comparison_results:
            st.markdown(
                f"""
                <div style="
                    padding:15px;
                    margin-bottom:10px;
                    border-radius:10px;
                    background-color:#1e1e1e;
                    border-left:8px solid {color};
                ">
                    <b>{marker}</b><br>
                    Patient Value: <b>{value}</b><br>
                    Normal Range: <b>{normal_range}</b><br>
                    Status: <span style="color:{color}; font-weight:bold;">{status}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    # -----------------------------
    # LOCATION-BASED CLINIC SEARCH
    # -----------------------------
    disease_type = detect_disease(abnormal_findings, summary)
    clinic_query = get_clinic_query(disease_type)

    if location and location.strip():
        search_query = f"{clinic_query} in {location}"
    else:
        search_query = clinic_query + " near me"

    map_embed_url = f"https://maps.google.com/maps?q={search_query.replace(' ', '+')}&output=embed"
    map_open_url  = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"

    st.markdown("## 🏥 Recommended Clinics Near You")
    st.info(f"Recommended specialist: {disease_type}")
    st.link_button("📍 Open Full Google Maps", map_open_url)
    components.iframe(map_embed_url, height=400)

    # -----------------------------
    # AMBULANCE ALERT FOR CRITICAL
    # -----------------------------
    if risk_level == "CRITICAL":
        st.error("🚑 CRITICAL CONDITION DETECTED")
        st.markdown("""
Immediate medical attention required.

Emergency Ambulance (India): **108**
        """)