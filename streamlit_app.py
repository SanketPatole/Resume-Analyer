import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json


class Page:
	def __init__(self):
		self.resume_object = None
		self.resume_content = ""
		self.jd_content = None
		self.submit_object = None
	
	def create_header(self, displayText="Header"):
		st.header(displayText)
	
	def create_subheader(self, displayText="Sub-Header"):
		st.subheader(displayText)
		
	def create_input_text(self, displayText="Input", height=150):
		return st.text_area(displayText, height=height)
	
	def create_error_message(self, displayText="Error"):
		st.error(displayText, icon="🚨")
	
	def create_file_widget(self, displayText="Choose a file...", fileType="pdf"):
		return st.file_uploader(displayText, type=fileType)
	
	def create_submit_button(self, displayText="Submit"):
		return st.button(displayText)

	def read_pdf_file(self):
		reader=pdf.PdfReader(self.resume_object)
		self.resume_content = ""
		for page in range(len(reader.pages)):
			page = reader.pages[page]
			self.resume_content += str(page.extract_text())
		
	def create_page(self):
		self.create_header(displayText="Upload your resume in PDF format.")
		self.resume_object = self.create_file_widget(fileType="pdf")
		self.create_header(displayText="Upload your resume in PDF format.")
		self.jd_content = self.create_input_text(displayText="Paste the job description here...", height=150)
		self.submit_object = self.create_submit_button(displayText="Submit")
		
		if self.resume_object is not None:
			try:
				self.read_pdf_file()
			except Exception as e:
				self.create_error_message(displayText=f"The pdf file is corrupted.\nError: {e}")
		
		if self.submit_object:
			if len(self.resume_content.strip()) == 0:
				self.create_error_message(displayText="Please provide a valid resume.")
			if len(self.jd_content.strip()) == 0:
				self.create_error_message(displayText="Please provide the job description.")
			if len(self.resume_content.strip()) > 0 and len(self.jd_content.strip()) > 0:
				self.create_subheader(displayText=self.resume_content)
	
page = Page()
page.create_page()
