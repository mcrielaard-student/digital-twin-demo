import streamlit as st

st.title("T1D Running Advisor")

st.write(
    "Enter your personal information and current glucose data "
    "to receive personalized running advice."
)

# Personal information
st.header("Personal information")

age = st.number_input(
    "Age",
    min_value=18,
    max_value=100,
    value=25,
    step=1
)

sex = st.selectbox(
    "Sex",
    [
        "Female",
        "Male"
    ]
)

height = st.number_input(
    "Height (cm)",
    min_value=120,
    max_value=220,
    value=175,
    step=1
)

weight = st.number_input(
    "Weight (kg)",
    min_value=30.0,
    max_value=200.0,
    value=70.0,
    step=0.5
)

# Calculate BMI
height_m = height / 100
bmi = weight / (height_m ** 2)


# Glucose information
st.header("Current glucose")

glucose = st.number_input(
    "Current glucose (mmol/L)",
    min_value=2.0,
    max_value=25.0,
    value=7.0,
    step=0.1
)

glucose_trend = st.selectbox(
    "Glucose trend",
    [
        "Rapidly falling",
        "Falling",
        "Stable",
        "Rising",
        "Rapidly rising"
    ]
)


# Get advice
if st.button("Get running advice"):

    st.subheader("Your information")

    st.write(f"Age: {age} years")
    st.write(f"Sex: {sex}")
    st.write(f"Height: {height} cm")
    st.write(f"Weight: {weight:.1f} kg")
    st.write(f"BMI: {bmi:.1f}")
    st.write(f"Starting glucose: {glucose:.1f} mmol/L")
    st.write(f"Glucose trend: {glucose_trend}")

    st.subheader("Running advice")

    # Temporary demo output
    # Later this will be replaced by the prediction/advice model

    st.success("Running is currently recommended.")

    st.write("Recommended duration: 30 minutes")
    st.write("Recommended intensity: Moderate")
    st.write("Estimated hypoglycemia risk: Low")

    st.subheader("Predicted glucose response")

    st.write("Predicted glucose after running: 5.8 mmol/L")

    st.info(
        "Demo output — the prediction and advice models are not connected yet."
    )