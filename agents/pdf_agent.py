from typing import Dict, Any
import PyPDF2
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .base_agent import BaseAgent
import json

class PDFAgent(BaseAgent):
    def __init__(self):
        super().__init__("pdf_agent")
        self.llm = ChatOpenAI(temperature=0)
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing business documents in PDF format.
            Extract the following information:
            1. Document type (invoice, policy, regulation, etc.)
            2. Key terms and conditions
            3. Important dates
            4. Monetary amounts (if any)
            5. Regulatory references (GDPR, FDA, etc.)
            
            Return your analysis in JSON format with these fields."""),
            ("human", "Analyze this document: {input_text}")
        ])

    def _extract_text_from_pdf(self, pdf_data: bytes) -> str:
        """Extract text content from PDF bytes."""
        try:
            pdf_file = PyPDF2.PdfReader(pdf_data)
            text = ""
            for page in pdf_file.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"Error extracting PDF text: {str(e)}"

    def process(self, input_data: bytes) -> Dict[str, Any]:
        """Process PDF content and extract relevant information."""
        # Extract text from PDF
        pdf_text = self._extract_text_from_pdf(input_data)
        
        # Get analysis from LLM
        chain = self.analysis_prompt | self.llm
        result = chain.invoke({"input_text": pdf_text})
        
        try:
            analysis = json.loads(result.content)
        except json.JSONDecodeError:
            analysis = {
                "document_type": "unknown",
                "key_terms": [],
                "important_dates": [],
                "monetary_amounts": [],
                "regulatory_references": []
            }

        # Check for high-value invoices or regulatory content
        action_triggered = None
        if analysis.get("document_type") == "invoice":
            amounts = analysis.get("monetary_amounts", [])
            if any(float(amount) > 10000 for amount in amounts if amount):
                action_triggered = "POST /risk_alert"
        
        if any(ref in ["GDPR", "FDA"] for ref in analysis.get("regulatory_references", [])):
            action_triggered = "POST /risk_alert"

        # Log the analysis
        self.log_activity(
            source="pdf",
            classification={"format": "pdf", "intent": analysis.get("document_type", "unknown")},
            extracted_fields=analysis,
            action_triggered=action_triggered
        )

        return analysis 