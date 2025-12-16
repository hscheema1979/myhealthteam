import streamlit as st

def show():
    st.title("Data Entry Dashboard")

    st.subheader("Add New Patient")
    with st.form("new_patient_form"):
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        date_of_birth = st.date_input("Date of Birth")
        submitted = st.form_submit_button("Add Patient")

        if submitted:
            # In a real application, you would save this to the database
            st.success(f"Successfully added patient: {first_name} {last_name}")