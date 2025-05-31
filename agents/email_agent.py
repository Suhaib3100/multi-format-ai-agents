from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .base_agent import BaseAgent
import json

class EmailAgent(BaseAgent):
    def __init__(self):
        super().__init__("email_agent")
        self.llm = ChatOpenAI(temperature=0)
        # Define the prompt template for email analysis.
        # Using "system" for instructions and "human" for the user's email input.
        # The {input_text} variable will contain the email content to analyze.
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing business emails.
            Extract the following information:
            1. Sender email address
            2. Urgency level (low, medium, high)
            3. Tone (polite, neutral, angry, threatening)
            4. Key points or requests
            
            Return your analysis in JSON format with these fields."""),
            ("human", "Analyze this email: {input_text}")
        ])

    def process(self, input_data: str) -> Dict[str, Any]:
        """Process email content and extract relevant information."""
        # Get analysis from LLM using the defined prompt.
        chain = self.analysis_prompt | self.llm
        result = chain.invoke({"input_text": input_data})
        
        try:
            # Parse the LLM's JSON output.
            analysis = json.loads(result.content)
        except json.JSONDecodeError:
            # Fallback analysis if LLM output isn't valid JSON.
            analysis = {
                "sender": "unknown",
                "urgency": "unknown",
                "tone": "unknown",
                "key_points": []
            }

        # Determine if escalation is needed based on the detected tone.
        action_triggered = None
        if analysis.get("tone") in ["angry", "threatening"]:
            action_triggered = "POST /crm/escalate"

        # Log the email analysis activity.
        self.log_activity(
            source="email",
            classification={"format": "email", "intent": "communication"},
            extracted_fields=analysis,
            action_triggered=action_triggered,
            agent_trace=["Email analysis completed", f"Tone detected: {analysis.get('tone')}"]
        )

        # Add action_triggered to the response if present for the ActionRouter.
        if action_triggered:
            analysis["action_triggered"] = action_triggered

        return analysis 