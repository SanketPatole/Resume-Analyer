import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json


def input_pdf_text(uploaded_file):
    reader=pdf.PdfReader(uploaded_file)
    text=""
    for page in range(len(reader.pages)):
        page=reader.pages[page]
        text+=str(page.extract_text())
    return text

st.header("Upload your resume in PDF format.")
uploaded_file = st.file_uploader("Choose a file...", type="pdf")

text = ""

if uploaded_file is not None:
	try:
		text=input_pdf_text(uploaded_file)
	except:
		st.error('The pdf file is corrupted.', icon="🚨")

st.header("Enter the job description")
job_description = st.text_area("Paste the job description here...", height=150)

submit = st.button("Submit")

if submit:
	if len(text.strip()) == 0:
		st.error('Please provide a valid resume.', icon="🚨")
	if len(job_description.strip()) == 0:
		st.error('Please provide the job description.', icon="🚨")
	if len(text.strip()) > 0 and len(job_description.strip()) > 0:
		st.subheader(text)

#st.subheader(text)
	


