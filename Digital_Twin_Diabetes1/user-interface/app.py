import streamlit as st

st.title("T1D Running Advisor")

st.write(
    "Enter your information and planned exercise below."
)

# Personal information
st.header("Personal information")

age = st.text_input("Age")
bmi = st.text_input("BMI")


# Glucose information
st.header("Current glucose")

glucose = st.text_input("Glucose (mg/dL)")

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


# Exercise information
st.header("Planned run")

duration = st.slider(
    "Duration (minutes)",
    min_value=10,
    max_value=120,
    value=30,
    step=5
)

intensity = st.selectbox(
    "Intensity",
    [
        "Low",
        "Moderate",
        "High"
    ]
)


# Button
if st.button("Get running advice"):

    if age == "" or bmi == "" or glucose == "":
        st.warning("Please fill in all fields.")

    else:
        st.subheader("Your planned run")

        st.write(f"Age: {age}")
        st.write(f"BMI: {bmi}")
        st.write(f"Starting glucose: {glucose} mg/dL")
        st.write(f"Glucose trend: {glucose_trend}")
        st.write(f"Duration: {duration} minutes")
        st.write(f"Intensity: {intensity}")

        st.subheader("Prediction")

        st.write("Predicted glucose after running: 95 mg/dL")
        st.write("Hypoglycemia risk: Low")

        st.info(
            "Demo output — prediction model not connected yet."
        )