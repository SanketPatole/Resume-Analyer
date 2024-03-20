import streamlit as st
import pandas as pd
import numpy as np

st.header("Upload your resume in PDF format.")
uploaded_file = st.file_uploader("Choose a file...", type="pdf")

st.header("Enter the job description")
job_description = st.text_area("Paste the job description here...", height=150)