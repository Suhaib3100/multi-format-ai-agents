from typing import Dict, Any
import PyPDF2
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .base_agent import BaseAgent
import json
import logging
import io

logger = logging.getLogger(__name__)

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
        self.max_text_length = 10000 # Maximum characters to send to the LLM

    def _extract_text_from_pdf(self, pdf_data: bytes) -> str:
        """Extract text content from PDF bytes."""
        try:
            # Use PyPDF2.PdfReader for reading
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
            text = ""
            # You could add logic here to limit pages if needed, but truncating later is simpler
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            return f"Error extracting PDF text: {str(e)}"

    def process(self, input_data: bytes) -> Dict[str, Any]:
        """Process PDF content and extract relevant information."""
        # Extract text from PDF
        pdf_text = self._extract_text_from_pdf(input_data)

        # Truncate text if it exceeds the maximum length
        original_length = len(pdf_text)
        if original_length > self.max_text_length:
            pdf_text = pdf_text[:self.max_text_length]
            logger.warning(f"Truncated PDF text from {original_length} to {self.max_text_length} characters.")
        
        # Get analysis from LLM
        chain = self.analysis_prompt | self.llm
        
        # Ensure input_text is a string
        input_payload = {"input_text": str(pdf_text)}

        try:
            result = chain.invoke(input_payload)
            analysis = json.loads(result.content)
        except Exception as e:
            logger.error(f"Error during LLM analysis or JSON parsing: {str(e)}")
            analysis = {
                "document_type": "unknown",
                "key_terms": [],
                "important_dates": [],
                "monetary_amounts": [],
                "regulatory_references": []
            }
            # Re-raise or handle specifically if needed, for now return default analysis

        # Check for high-value invoices or regulatory content (basic example)
        action_triggered = None
        if analysis.get("document_type") == "invoice":
            amounts = analysis.get("monetary_amounts", [])
            # Ensure amounts are treated as numbers for comparison
            numeric_amounts = []
            for amount in amounts:
                try:
                    numeric_amounts.append(float(amount))
                except (ValueError, TypeError):
                    continue # Skip if not a valid number

            if any(amount > 10000 for amount in numeric_amounts):
                action_triggered = "POST /risk_alert"

        # Basic check for regulatory references
        if any(ref in "GDPR FDA" for ref in analysis.get("regulatory_references", [])):
             action_triggered = "POST /risk_alert"

        # Log the analysis
        self.log_activity(
            source="pdf",
            classification={"format": "pdf", "intent": analysis.get("document_type", "unknown")},
            extracted_fields=analysis,
            action_triggered=action_triggered
        )

        return analysis 