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
        # Prompt template for PDF analysis. Uses a 'human' message for the input text.
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing business documents in PDF format.
            Extract the following information:
            1. Document type (invoice, policy, regulation, etc.)
            2. Key terms and conditions
            3. Important dates
            4. Monetary amounts (if any)
            5. Regulatory references (GDPR, FDA, etc.)
            
            Return your analysis in JSON format with these fields."""
            ),
            ("human", "Analyze this document: {input_text}")
        ])
        # Limit on the number of characters sent to the language model to avoid exceeding token limits.
        self.max_text_length = 2000 

    def _extract_text_from_pdf(self, pdf_data: bytes) -> str:
        """Extract text content from PDF bytes."""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            return f"Error extracting PDF text: {str(e)}"

    def process(self, input_data: bytes) -> Dict[str, Any]:
        """Process PDF content and extract relevant information using LLM."""
        pdf_text = self._extract_text_from_pdf(input_data)

        # Apply the text length limit before sending to the LLM.
        original_length = len(pdf_text)
        if original_length > self.max_text_length:
            pdf_text = pdf_text[:self.max_text_length]
            logger.warning(f"Truncated PDF text from {original_length} to {self.max_text_length} characters.")

        logger.info(f"Length of text being sent to LLM: {len(pdf_text)} characters.")
        
        chain = self.analysis_prompt | self.llm
        input_payload = {"input_text": str(pdf_text)}

        try:
            # Invoke the language model chain and parse the JSON response.
            result = chain.invoke(input_payload)
            analysis = json.loads(result.content)
        except Exception as e:
            logger.error(f"Error during LLM analysis or JSON parsing: {str(e)}")
            # Provide a default empty analysis on error.
            analysis = {
                "document_type": "unknown",
                "key_terms": [],
                "important_dates": [],
                "monetary_amounts": [],
                "regulatory_references": []
            }

        # Determine if a risk-based action should be triggered.
        action_triggered = None
        # (Basic example logic - can be expanded based on analysis content)
        if analysis.get("document_type") == "invoice":
            amounts = analysis.get("monetary_amounts", [])
            numeric_amounts = []
            for amount in amounts:
                try:
                    numeric_amounts.append(float(amount))
                except (ValueError, TypeError):
                    continue 

            if any(amount > 10000 for amount in numeric_amounts):
                action_triggered = "POST /risk_alert"

        if any(ref in "GDPR FDA" for ref in analysis.get("regulatory_references", [])):
             action_triggered = "POST /risk_alert"

        # Log the PDF analysis activity.
        self.log_activity(
            source="pdf",
            classification={"format": "pdf", "intent": analysis.get("document_type", "unknown")},
            extracted_fields=analysis,
            action_triggered=action_triggered
        )

        return analysis 