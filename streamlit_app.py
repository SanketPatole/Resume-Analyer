import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
import openai
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.document_loaders import CSVLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS


class GenAI_Wrpapper:
	def __init__(self, chat_client='chatgpt3.5'):
		self.is_gemini = False
		if chat_client == 'chatgpt3.5':
			self.chat_client = ChatOpenAI(model="gpt-3.5-turbo")
		elif chat_client == 'chatgpt3.5turbo':
			self.chat_client = ChatOpenAI(model="gpt-3.5-turbo-instruct")
		elif chat_client == 'chatgpt4':
			self.chat_client = ChatOpenAI(model="gpt-4")
		elif chat_client == 'gemini':
			genai.configure()
			self.chat_client = genai.GenerativeModel('gemini-pro')
			self.is_gemini = True
		self.embedding = OpenAIEmbeddings()
	
	def get_document_splits(self, file_data, chunk_size=1500, chunk_overlap=150):
		splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
		splits = splitter.split_text(file_data)
		return splits

	def create_vectordb_from_document_splits(self, document_splits):
		return FAISS.from_texts(document_splits, embedding=self.embedding)
	  
	def get_output_parser(self, ):
		strengths = ResponseSchema(name="strengths", description="Strengths of the candidate")
		weaknesses = ResponseSchema(name="weaknesses", description="Weaknesses of the candidate.")
		summary = ResponseSchema(name="summary", description="Short summary of the analysis mentioning eligibility of the candidate.")
		is_shortlisted = ResponseSchema(name="is_shortlisted", description="Do candidate's skills match with required skills? (Yes/No)")
		reason = ResponseSchema(name="reason", description="Reason in one sentence, why the candidate is selected or rejected.")
		return StructuredOutputParser.from_response_schemas([strengths, weaknesses, summary, is_shortlisted, reason])

	def get_prompt_template(self, ):
		prompt_template_text = """
		You will be provided with a Job Description enclosed within {delimiter_job_description} delimiter.
		You'll also be provided with skills of the candidate enclosed within {delimiter_skills} delimiter.

		Depending upon these two inputs, please provide the skill gap analysis for the employer to short-list resume.
		Please make sure that the analysis is concise and to the point.

		{delimiter_skills}{context}{delimiter_skills}

		{delimiter_job_description}{job_description}{delimiter_job_description}

		{instructions}
		"""
		return PromptTemplate(template=prompt_template_text,
							input_variables=["context", "job_description", "delimiter_skills", "delimiter_job_description", "instructions"])

	def get_qa_chain(self, prompt):
		return load_qa_chain(llm=self.chat_client, chain_type="stuff", prompt=prompt)
		
	def run_qa_chain(self, resume_text, job_description_text):
		query = "What are the skills and educational qualifications of the candidate?"
		prompt = self.get_prompt_template()
		output_parser = self.get_output_parser()
		instructions = output_parser.get_format_instructions()
		document_splits = self.get_document_splits(resume_text, chunk_size=1500, chunk_overlap=150)
		vectordb = self.create_vectordb_from_document_splits(document_splits)
		skills = vectordb.similarity_search(query, k=2)
		response = ""
		if self.is_gemini == False:
			chain = self.get_qa_chain(prompt)
			prompt_inputs = {"input_documents": skills, "job_description": job_description_text,
						   "delimiter_skills": "###", "delimiter_job_description": "$$$", "instructions": instructions}
			response = chain(prompt_inputs, return_only_outputs=True)
			response = response["output_text"]
		else:
			response=self.chat_client.generate_content(prompt.format(delimiter_job_description="$$$",
			delimiter_skills="###", context=skills, job_description=job_description_text, instructions=instructions)).text
		response_dict = output_parser.parse(response)
		return response_dict

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
		
	def display_candidate_eval_summary(self, results):
		st.write("### Candidate Evaluation Summary")
		st.write("#### Strengths")
		st.write(results['strengths'])
		st.write("#### Weaknesses")
		st.write(results['weaknesses'])
		st.write("#### Summary")
		st.write(results['summary'])
		st.write("#### Shortlisted?")
		st.write("Yes" if results['is_shortlisted'] == 'Yes' else "No")
		st.write(f"#### Reason for candidate's {'selection' if results['is_shortlisted'] == 'Yes' else 'rejection'}")
		st.write(results['reason'])
		
	def get_response(self, chat_client='chatgpt3.5'):
		response = GenAI_Wrpapper(chat_client).run_qa_chain(self.resume_content, self.jd_content)
		self.display_candidate_eval_summary(response)
		
	def create_page(self):
		alternative_model = {"chatgpt3.5": "gemini", "gemini": "chatgpt3.5"}
		chat_client = st.selectbox("Choose a model:", ("chatgpt3.5", "gemini"))
		self.create_header(displayText="Upload your resume in PDF format.")
		self.resume_object = self.create_file_widget(fileType="pdf")
		self.create_header(displayText="Paste the job description here...")
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
				try:
					self.get_response(chat_client=chat_client)
				except Exception as e1:
					self.create_error_message(displayText=f"Chatgpt failed for {e1}")
					try:
						self.get_response(chat_client=alternative_model[chat_client])
					except Exception as e2:
						self.create_error_message(displayText=f"Unble to connect to ChatBot at his moment. Please try again later.")
						self.create_error_message(displayText=f"Gemini failed for {e2}")
page = Page()
page.create_page()
