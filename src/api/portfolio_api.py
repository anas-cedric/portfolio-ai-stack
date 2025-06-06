"""
Portfolio Recommendation API.

This module provides API endpoints for generating portfolio recommendations using OpenAI.
"""

import os
import openai
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, Request, status, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError
import logging
import json
import re
from datetime import datetime
import uuid
from pathlib import Path
from dotenv import load_dotenv
from src.utils.openai_client import openai_client, OpenAIClient  # import class for extra model
from src.prompts.financial_prompts import FinancialPrompts # Adjusted import
from src.utils.auth import get_api_key # Corrected absolute import

# --- Import Glide Path Data ---
from src.data.glide_path_allocations import GLIDE_PATH_ALLOCATIONS
import json # For formatting the holdings/allocations nicely

# --- Ticker to Name Mapping (Expand as needed) ---
TICKER_NAMES = {
    "VTI": "Vanguard Total Stock Market ETF",
    "VUG": "Vanguard Growth ETF",
    "VBR": "Vanguard Small-Cap Value ETF",
    "VEA": "Vanguard FTSE Developed Markets ETF",
    "VSS": "Vanguard FTSE All-World ex-US Small-Cap ETF",
    "VWO": "Vanguard FTSE Emerging Markets ETF",
    "VNQ": "Vanguard Real Estate ETF",
    "VNQI": "Vanguard Global ex-U.S. Real Estate ETF",
    "BND": "Vanguard Total Bond Market ETF",
    "BNDX": "Vanguard Total International Bond ETF",
    "VTIP": "Vanguard Short-Term Inflation-Protected Securities ETF",
    "CASH": "Cash", # Added Cash
    # Add any other tickers present in your CSVs
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# User records storage path
USER_RECORDS_PATH = Path("data/user_records.json")
USER_RECORDS_PATH.parent.mkdir(exist_ok=True)

def save_user_record(user_data: dict) -> str:
    """Save user record to JSON file. Returns user ID."""
    user_id = str(uuid.uuid4())
    record = {
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        **user_data
    }
    
    # Load existing records
    records = []
    if USER_RECORDS_PATH.exists():
        try:
            with open(USER_RECORDS_PATH, 'r') as f:
                records = json.load(f)
        except Exception as e:
            logger.error(f"Error loading user records: {e}")
    
    # Append new record
    records.append(record)
    
    # Save updated records
    try:
        with open(USER_RECORDS_PATH, 'w') as f:
            json.dump(records, f, indent=2)
        logger.info(f"Saved user record for {user_data.get('firstName', 'Unknown')} {user_data.get('lastName', 'Unknown')}")
    except Exception as e:
        logger.error(f"Error saving user record: {e}")
    
    return user_id

# --- Risk Tolerance Questionnaire Data ---
RISK_QUESTIONNAIRE = """
Please answer the following questions to help determine your risk tolerance. Respond with the question number and your chosen letter (e.g., '1a, 2c, 3b, ...').

1. In general, how would your best friend describe you as a risk taker?
   a. A real gambler
   b. Willing to take risks after completing adequate research
   c. Cautious
   d. A real risk avoider

2. You are on a TV game show and can choose one of the following; which would you take?
   a. $1,000 in cash
   b. A 50% chance at winning $5,000
   c. A 25% chance at winning $10,000
   d. A 5% chance at winning $100,000

3. You have just finished saving for a “once-in-a-lifetime” vacation. Three weeks before you plan to leave, you lose your job. You would:
   a. Cancel the vacation
   b. Take a much more modest vacation
   c. Go as scheduled, reasoning that you need the time to prepare for a job search
   d. Extend your vacation, because this might be your last chance to go first-class

4. If you unexpectedly received $20,000 to invest, what would you do?
   a. Deposit it in a bank account, money market account, or insured CD
   b. Invest it in safe high-quality bonds or bond mutual funds
   c. Invest it in stocks or stock mutual funds

5. In terms of experience, how comfortable are you investing in stocks or stock mutual funds?
   a. Not at all comfortable
   b. Somewhat comfortable
   c. Very Comfortable

6. When you think of the word “risk,” which of the following words comes to mind first?
   a. Loss
   b. Uncertainty
   c. Opportunity
   d. Thrill

7. Some experts are predicting prices of assets such as gold, jewels, collectibles, and real estate (hard assets) to increase in value; bond prices may fall, however, experts tend to agree that government bonds are relatively safe. Most of your investment assets are now in high-interest government bonds. What would you do?
   a. Hold the bonds
   b. Sell the bonds, put half the proceeds into money market accounts, and the other half into hard assets
   c. Sell the bonds and put the total proceeds into hard assets
   d. Sell the bonds, put all the money into hard assets, and borrow additional money to buy more

8. Given the best and worst case returns of the four investment choices below, which would you prefer?
   a. $200 gain best case; $0 gain/loss worst case
   b. $800 gain best case, $200 loss worst case
   c. $2,600 gain best case, $800 loss worst case
   d. $4,800 gain best case, $2,400 loss worst case

9. In addition to whatever you own, you have been given $1,000. You are now asked to choose between:
   a. A sure gain of $500
   b. A 50% chance to gain $1,000 and a 50% chance to gain nothing.
   c. A 25% chance to gain $2,000 and a 75% chance to gain nothing.
   d. A 10% chance to gain $5,000 and a 90% chance to gain nothing.
   e. A 5% chance to gain $10,000 and a 95% chance to gain nothing.

10. In addition to whatever you own, you have been given $2,000. You are now asked to choose between:
   a. A sure loss of $500
   b. A 50% chance to lose $1,000 and a 50% chance to lose nothing.
   c. A 25% chance to lose $2,500 and a 75% chance to lose nothing.
   d. A 10% chance to lose $10,000 and a 90% chance to lose nothing.

11. Suppose a relative left you an inheritance of $100,000, stipulating in the will that you invest ALL the money in ONE of the following choices. Which one would you select?
   a. A savings account or money market mutual fund
   b. A mutual fund that owns stocks and bonds
   c. A portfolio of 15 common stocks
   d. Commodities like gold, silver, and oil

12. If you had to invest $20,000, which of the following investment choices would you find most appealing?
   a. 60% low-risk, 30% medium-risk, 10% high-risk
   b. 30% low-risk, 40% medium-risk, 30% high-risk
   c. 10% low-risk, 40% medium-risk, 50% high-risk

13. Your friend is raising money to fund an exploratory gold-mining venture with a 20% chance of success and huge upside. How much would you invest?
   a. Nothing
   b. One month’s salary
   c. Three months’ salary
   d. Six months’ salary
"""

RISK_SCORING_RULES = {
    1: {'a': 4, 'b': 3, 'c': 2, 'd': 1},
    2: {'a': 1, 'b': 2, 'c': 3, 'd': 4},
    3: {'a': 1, 'b': 2, 'c': 3, 'd': 4},
    4: {'a': 1, 'b': 2, 'c': 3},
    5: {'a': 1, 'b': 2, 'c': 3},
    6: {'a': 1, 'b': 2, 'c': 3, 'd': 4},
    7: {'a': 1, 'b': 2, 'c': 3, 'd': 4},
    8: {'a': 1, 'b': 2, 'c': 3, 'd': 4},
    9: {'a': 1, 'b': 2},
    10: {'a': 1, 'b': 2}, 
    11: {'a': 1, 'b': 2, 'c': 3, 'd': 4},
    12: {'a': 1, 'b': 2, 'c': 3}, # Updated to 3 options (a-c)
    13: {'a': 1, 'b': 2, 'c': 3, 'd': 4}
}

RISK_LEVEL_MAPPING = {
    (33, 47): "High",          # High tolerance
    (29, 32): "Above-Avg",     # Above-average tolerance
    (23, 28): "Moderate",      # Average/moderate tolerance
    (19, 22): "Below-Avg",     # Below-average tolerance
    (0, 18): "Low"            # Low tolerance (Adjusted lower bound to 0)
}

# Map risk levels from questionnaire to glide path keys
# Ensure these keys exactly match the keys in GLIDE_PATH_ALLOCATIONS
QUESTIONNAIRE_TO_GLIDE_PATH_MAP = {
    "High": "High",
    "Above-Avg": "Above-Avg",
    "Moderate": "Moderate",
    "Below-Avg": "Below-Avg",
    "Low": "Low"
}

def calculate_risk_score_and_level(answers_str: str) -> tuple[int, str | None]:
    """Calculates both the risk score and tolerance level. Returns (score, level)."""
    total_score = 0
    parsed_answers = {}
    
    try:
        answer_pairs = answers_str.lower().replace(" ", "").split(',')
        for pair in answer_pairs:
            if not pair:
                continue
            split_index = -1
            for i, char in enumerate(pair):
                if char.isalpha():
                    split_index = i
                    break
            
            if split_index == -1 or split_index == 0:
                logger.warning(f"Could not parse answer pair: '{pair}'")
                continue
                
            q_num_str = pair[:split_index]
            ans_letter = pair[split_index:]
            
            if len(ans_letter) > 1:
                logger.warning(f"Multiple letters in answer for question {q_num_str}: '{ans_letter}'. Using first letter.")
                ans_letter = ans_letter[0]
            
            q_num = int(q_num_str)
            
            if q_num not in RISK_SCORING_RULES:
                logger.warning(f"Ignoring answer for invalid question number: {q_num}")
                continue
            
            rules = RISK_SCORING_RULES[q_num]
            if ans_letter not in rules:
                logger.warning(f"Ignoring invalid answer '{ans_letter}' for question {q_num}")
                continue
            
            score = rules[ans_letter]
            total_score += score
            parsed_answers[q_num] = ans_letter
        
        logger.info(f"Calculated risk score: {total_score} from answers: {parsed_answers}")
        
        # Map to risk level
        for (low, high), level in RISK_LEVEL_MAPPING.items():
            if low <= total_score <= high:
                logger.info(f"Mapped score {total_score} to risk level: {level}")
                return total_score, level
        
        logger.warning(f"Risk score {total_score} does not fall into any defined range.")
        return total_score, None
        
    except Exception as e:
        logger.error(f"Error calculating risk level: {e}")
        return 0, None

def calculate_risk_level(answers_str: str) -> str | None:
    """Calculates the risk tolerance level based on questionnaire answers."""
    total_score = 0
    parsed_answers = {}
    expected_questions = set(RISK_SCORING_RULES.keys())
    answered_questions = set()

    try:
        # Parse answers like "1a, 2c, 3b ..."
        answer_pairs = answers_str.lower().replace(" ", "").split(',')
        for pair in answer_pairs:
            if not pair:
                continue
            # Find the split point between number and letter
            split_index = -1
            for i, char in enumerate(pair):
                if char.isalpha():
                    split_index = i
                    break
            
            if split_index == -1 or split_index == 0:
                 logger.warning(f"Could not parse answer pair: '{pair}'")
                 continue # Skip malformed pair
                 
            q_num_str = pair[:split_index]
            ans_letter = pair[split_index:] # Keep case if needed, though rules are lowercase keys

            if len(ans_letter) > 1:
                 logger.warning(f"Multiple letters in answer for question {q_num_str}: '{ans_letter}'. Using first letter.")
                 ans_letter = ans_letter[0]

            q_num = int(q_num_str)

            if q_num not in RISK_SCORING_RULES:
                logger.warning(f"Ignoring answer for invalid question number: {q_num}")
                continue

            rules = RISK_SCORING_RULES[q_num]
            if ans_letter not in rules:
                logger.warning(f"Ignoring invalid answer '{ans_letter}' for question {q_num}")
                continue

            # Special handling for averaging Q9 and Q10 if needed (currently not implemented as per source)
            # if q_num == 9 or q_num == 10:
            #     # Logic to store and average later if required by '*' rule
            #     pass 
                
            score = rules[ans_letter]
            total_score += score
            answered_questions.add(q_num)
            parsed_answers[q_num] = ans_letter

        # Check if all questions were answered
        missing_questions = expected_questions - answered_questions
        if missing_questions:
            logger.warning(f"Missing answers for questions: {sorted(list(missing_questions))}")
            # Decide if partial scoring is allowed or return None
            # For now, require all questions
            return None 

        logger.info(f"Calculated risk score: {total_score} from answers: {parsed_answers}")

        # Map score to level
        for (min_score, max_score), level in RISK_LEVEL_MAPPING.items():
            if min_score <= total_score <= max_score:
                mapped_level = QUESTIONNAIRE_TO_GLIDE_PATH_MAP.get(level)
                if mapped_level:
                    logger.info(f"Mapped score {total_score} to risk level: {mapped_level}")
                    return mapped_level
                else:
                     logger.error(f"Internal Error: Questionnaire level '{level}' not found in QUESTIONNAIRE_TO_GLIDE_PATH_MAP.")
                     return None # Should not happen if map is correct
        
        logger.warning(f"Score {total_score} did not fall into any defined risk level range.")
        return None # Score out of range

    except Exception as e:
        logger.error(f"Error parsing risk answers '{answers_str}': {e}", exc_info=True)
        return None

# --- Helper Function ---
def get_glide_path_allocation(age: int, risk_tolerance: str) -> dict | None:
    """Finds the appropriate allocation dictionary from GLIDE_PATH_ALLOCATIONS
    based on age and risk tolerance."""
    # Ensure age is an integer
    if not isinstance(age, int):
        try:
            age = int(age)
        except (ValueError, TypeError):
            logger.warning(f"Invalid age provided for lookup: {age}. Cannot determine allocation.")
            return None

    # Normalize risk tolerance key (e.g., handle case sensitivity if needed)
    normalized_risk = risk_tolerance # Add .lower() or .title() if keys in dict are different case
    risk_level_data = GLIDE_PATH_ALLOCATIONS.get(normalized_risk)

    if not risk_level_data:
        logger.warning(f"Risk tolerance level '{risk_tolerance}' (Normalized: '{normalized_risk}') not found in allocations.")
        # Log available keys for debugging
        logger.debug(f"Available risk keys: {list(GLIDE_PATH_ALLOCATIONS.keys())}")
        return None

    # Find the matching age range
    for (min_age, max_age), allocation in risk_level_data.items():
        if min_age <= age <= max_age:
            logger.info(f"Found allocation for age {age}, risk '{risk_tolerance}': Range ({min_age}-{max_age})")
            return allocation # Found the matching age range

    logger.warning(f"No matching age range found for age {age} within risk level '{risk_tolerance}'.")
    return None # Age not found within any range for this risk level

# Define required fields for generation
REQUIRED_FIELDS_FOR_GENERATION = [
    "age", "income", "risk_tolerance", "investment_goals", 
    "time_horizon", "initial_investment", "monthly_contribution"
    # Optional fields handled later: "sector_preferences", "avoid_sectors"
]

# Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Portfolio Advisor API",
    description="API for generating portfolio recommendations using OpenAI",
    version="1.0.0",
)

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validate API key middleware
async def verify_api_key(x_api_key: str = Header(None)):
    api_key = os.getenv("API_KEY")
    if not api_key:
        logger.warning("API_KEY not set in environment variables")
        raise HTTPException(status_code=500, detail="API not properly configured")
    
    if x_api_key != api_key:
        logger.warning("Invalid API key provided")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return x_api_key

# Input models
class InvestmentGoals(BaseModel):
    retirement: bool = False
    growth: bool = False
    income: bool = False
    preservation: bool = False

class SectorPreferences(BaseModel):
    technology: bool = False
    healthcare: bool = False
    financial: bool = False
    consumer: bool = False
    energy: bool = False
    utilities: bool = False

class AvoidSectors(BaseModel):
    tobacco: bool = False
    gambling: bool = False
    weapons: bool = False
    fossil_fuels: bool = False

class PortfolioRequest(BaseModel):
    age: int = Field(..., ge=18, le=100)
    income: str = Field(..., description="Income level: low, mid-range, high, very-high")
    risk_tolerance: str = Field(..., description="Risk tolerance: very-low, low, moderate, high, very-high")
    investment_goals: List[str] = Field([], description="List of investment goals")
    time_horizon: str = Field(..., description="Investment time horizon: short-term, medium-term, long-term")
    initial_investment: float = Field(..., gt=0)
    monthly_contribution: float = Field(..., ge=0)
    sector_preferences: List[str] = Field([], description="List of preferred sectors")
    avoid_sectors: List[str] = Field([], description="List of sectors to avoid")

# Output models
class PortfolioHolding(BaseModel):
    ticker: str
    name: str
    value: float
    percentage: float

class PortfolioProjection(BaseModel):
    years: List[int]
    values: List[float]

class PortfolioRecommendation(BaseModel):
    title: str
    description: str

class PortfolioResponse(BaseModel):
    total_value: float
    holdings: List[PortfolioHolding]
    allocations: Dict[str, float]
    projections: PortfolioProjection
    recommendations: List[PortfolioRecommendation]
    analysis: str
    user_profile: Dict[str, Any]

class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    conversation_id: str
    user_message: str
    conversation_history: Optional[List[ChatMessage]] = None # Use ChatMessage model
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            # Conversation state: initial -> gather_risk -> gather_details -> generate
            "conversation_state": "initial",
            "user_profile": { # Store gathered age, investment, horizon
                 "age": None,
                 "initial_investment": None,
                 "time_horizon": None
            },
            "risk_score": None, # If calculate_risk_level provides it
            "derived_risk_level": None, # Store level from questionnaire
            # Sequential questionnaire tracking
            "risk_question_index": 1,  # 1-based index
            "risk_answers": {}  # {"1": "a", ...}
        }
    )

class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    conversation_history: Optional[List[ChatMessage]] = None
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            # Conversation state: initial -> gather_risk -> gather_details -> generate
            "conversation_state": "initial",
            "user_profile": { # Store gathered age, investment, horizon
                 "age": None,
                 "initial_investment": None,
                 "time_horizon": None
            },
            "risk_score": None, # If calculate_risk_level provides it
            "derived_risk_level": None, # Store level from questionnaire
            # Sequential questionnaire tracking
            "risk_question_index": 1,  # 1-based index
            "risk_answers": {}  # {"1": "a", ...}
        }
    )
    # Structured portfolio data returned when generation completes
    updated_portfolio: Optional[Dict[str, Any]] = None

# --- Wizard Request Model ---
class WizardRequest(BaseModel):
    answers: Dict[str, str] = Field(..., description="Dictionary of question IDs to chosen letter answers, e.g., {'q1': 'a', 'q2': 'c'}")
    age: Optional[int] = Field(None, description="Optional age of the user.")
    firstName: Optional[str] = Field(None, description="User's first name")
    lastName: Optional[str] = Field(None, description="User's last name")
    birthday: Optional[str] = Field(None, description="User's birthday in YYYY-MM-DD format")

# --- New Models for Portfolio Update --- 
class BackendUserProfile(BaseModel):
    age: Optional[int] = None
    income: Optional[str] = None
    risk_tolerance: Optional[str] = None
    investment_goals: Optional[List[str]] = None
    time_horizon: Optional[str] = None
    initial_investment: Optional[float] = None
    monthly_contribution: Optional[float] = None
    sector_preferences: Optional[List[str]] = None
    avoid_sectors: Optional[List[str]] = None

class BackendPortfolioData(BaseModel):
    total_value: float
    holdings: List[PortfolioHolding]
    allocations: Dict[str, float]
    projections: Optional[PortfolioProjection] = None
    recommendations: Optional[List[PortfolioRecommendation]] = None
    analysis: Optional[str] = None

class NestedPortfolioInput(BaseModel):
    portfolioData: BackendPortfolioData
    userPreferences: BackendUserProfile

class PortfolioUpdateRequest(BaseModel):
    current_portfolio: NestedPortfolioInput
    chat_history: List[ChatMessage]

# --- Helper Functions ---
def create_details_extraction_prompt(user_message: str, current_profile: dict, derived_risk_level: str) -> str:
    """Creates a prompt for the LLM to extract age, investment, and horizon."""
    prompt = f"""You are an assistant helping gather information for financial portfolio generation.
The user's risk tolerance has been determined as '{derived_risk_level}'.

Based on the user's latest message, extract the following information:
- age (integer)
- initial_investment (float, numerical value only)
- time_horizon (string, e.g., '5 years', 'long-term')

User message: "{user_message}"

Respond ONLY with a valid JSON object containing these keys. If a value is not mentioned or unclear, set its value to null in the JSON.
Example response: {{"age": 35, "initial_investment": 50000.0, "time_horizon": "10 years"}}
Example response if only age mentioned: {{"age": 42, "initial_investment": null, "time_horizon": null}}

JSON response:"""
    return prompt

def extract_json_from_response(response_text: str) -> dict | None:
    """Extracts a JSON object from the LLM's response string."""
    # Try finding JSON within ```json ... ``` blocks first
    match = re.search(r'```json\n({.*?})\n```', response_text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # Fallback: find the first '{' and last '}'
        start = response_text.find('{')
        end = response_text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = response_text[start:end+1]
        else:
            logger.warning("Could not find JSON block in response.")
            return None
    
    try:
        # Clean potential artifacts before parsing
        cleaned_json_str = re.sub(r'\n', '\n', json_str) # Ensure newlines are literals if escaped
        parsed_json = json.loads(cleaned_json_str)
        logger.info(f"Successfully extracted JSON: {parsed_json}")
        return parsed_json
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode extracted JSON string: {e}\nString: '{json_str}'")
        return None

# --- Ticker to Name Mapping (Expand as needed) ---
TICKER_NAMES = {
    "VTI": "Vanguard Total Stock Market ETF",
    "VUG": "Vanguard Growth ETF",
    "VBR": "Vanguard Small-Cap Value ETF",
    "VEA": "Vanguard FTSE Developed Markets ETF",
    "VSS": "Vanguard FTSE All-World ex-US Small-Cap ETF",
    "VWO": "Vanguard FTSE Emerging Markets ETF",
    "VNQ": "Vanguard Real Estate ETF",
    "VNQI": "Vanguard Global ex-U.S. Real Estate ETF",
    "BND": "Vanguard Total Bond Market ETF",
    "BNDX": "Vanguard Total International Bond ETF",
    "VTIP": "Vanguard Short-Term Inflation-Protected Securities ETF",
    "CASH": "Cash", # Added Cash
    # Add any other tickers present in your CSVs
}

# --- Sequential Risk Questions (for one-by-one flow) ---
RISK_QUESTIONS = [
    "1. In general, how would your best friend describe you as a risk taker?\n   a. A real gambler\n   b. Willing to take risks after completing adequate research\n   c. Cautious\n   d. A real risk avoider",
    "2. You are on a TV game show and can choose one of the following; which would you take?\n   a. $1,000 in cash\n   b. A 50% chance at winning $5,000\n   c. A 25% chance at winning $10,000\n   d. A 5% chance at winning $100,000",
    "3. You have just finished saving for a once-in-a-lifetime vacation. Three weeks before you plan to leave, you lose your job. You would:\n   a. Cancel the vacation\n   b. Take a much more modest vacation\n   c. Go as scheduled, reasoning that you need the time to prepare for a job search\n   d. Extend your vacation, because this might be your last chance to go first-class",
    "4. If you unexpectedly received $20,000 to invest, what would you do?\n   a. Deposit it in a bank account, money market account, or insured CD\n   b. Invest it in safe high-quality bonds or bond mutual funds\n   c. Invest it in stocks or stock mutual funds",
    "5. In terms of experience, how comfortable are you investing in stocks or stock mutual funds?\n   a. Not at all comfortable\n   b. Somewhat comfortable\n   c. Very comfortable",
    "6. When you think of the word ‘risk,’ which of the following words comes to mind first?\n   a. Loss\n   b. Uncertainty\n   c. Opportunity\n   d. Thrill",
    "7. Some experts are predicting prices of assets such as gold, jewels, collectibles, and real estate to increase in value; bond prices may fall. Most of your investment assets are now in high-interest government bonds. What would you do?\n   a. Hold the bonds\n   b. Sell the bonds, put half the proceeds into money market accounts, and the other half into hard assets\n   c. Sell the bonds and put the total proceeds into hard assets\n   d. Sell the bonds, put all the money into hard assets, and borrow additional money to buy more",
    "8. Given the best and worst case returns of the four investment choices below, which would you prefer?\n   a. $200 gain best case; $0 gain/loss worst case\n   b. $800 gain best case; $200 loss worst case\n   c. $2,600 gain best case; $800 loss worst case\n   d. $4,800 gain best case; $2,400 loss worst case",
    "9. In addition to whatever you own, you have been given $1,000. You are now asked to choose between:\n   a. A sure gain of $500\n   b. A 50% chance to gain $1,000 and a 50% chance to gain nothing.\n   c. A 25% chance to gain $2,000 and a 75% chance to gain nothing.\n   d. A 10% chance to gain $5,000 and a 90% chance to gain nothing.\n   e. A 5% chance to gain $10,000 and a 95% chance to gain nothing.",
    "10. In addition to whatever you own, you have been given $2,000. You are now asked to choose between:\n   a. A sure loss of $500\n   b. A 50% chance to lose $1,000 and a 50% chance to lose nothing.\n   c. A 25% chance to lose $2,500 and a 75% chance to lose nothing.\n   d. A 10% chance to lose $10,000 and a 90% chance to lose nothing.",
    "11. Suppose a relative left you an inheritance of $100,000, stipulating that you invest ALL the money in ONE of the following choices. Which one would you select?\n   a. A savings account or money market mutual fund\n   b. A mutual fund that owns stocks and bonds\n   c. A portfolio of 15 common stocks\n   d. Commodities like gold, silver, and oil",
    "12. If you had to invest $20,000, which investment choice would you find most appealing?\n   a. 60% low-risk, 30% medium-risk, 10% high-risk\n   b. 30% low-risk, 40% medium-risk, 30% high-risk\n   c. 10% low-risk, 40% medium-risk, 50% high-risk",
    "13. Your friend is raising money to fund an exploratory gold-mining venture with a 20% chance of success and huge upside. How much would you invest?\n   a. Nothing\n   b. One month’s salary\n   c. Three months’ salary\n   d. Six months’ salary"
]

# Helper to extract single letter answer
def extract_single_choice(answer_str: str) -> str | None:
    match = re.search(r"[abcd]", answer_str.lower())
    return match.group(0) if match else None

# API Endpoints
@app.post("/api/portfolio-chat", response_model=ChatResponse)
async def process_portfolio_chat(
    request: ChatRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Handles the chat conversation for portfolio recommendations.
    Manages state: sends questionnaire, processes answers, gathers details, generates portfolio.
    """
    logger.info(f"Processing portfolio chat request for conversation_id: {request.conversation_id}")
    logger.debug(f"Received chat request: {request}")

    conversation_history = request.conversation_history or []
    user_message = request.user_message
    # Ensure metadata is a mutable dictionary and handle potential None
    metadata = request.metadata.copy() if isinstance(request.metadata, dict) else ChatRequest.__fields__['metadata'].default_factory()
    conversation_state = metadata.get("conversation_state", "initial")
    user_profile = metadata.get("user_profile", {})
    derived_risk_level = metadata.get("derived_risk_level")

    # Will hold the structured portfolio JSON after successful generation
    updated_portfolio_data: Optional[Dict[str, Any]] = None

    response_message = ""
    next_state = conversation_state # Default to staying in the same stage

    try:
        # --- State: Initial -> Start Risk Questionnaire ---
        if conversation_state == "initial":
            logger.info("State: initial. Starting sequential risk questionnaire.")
            # Reset questionnaire progress
            metadata["risk_question_index"] = 1
            metadata["risk_answers"] = {}
            response_message = (
                "Great! Let's assess your risk tolerance. Please answer with just the letter (a, b, c, or d).\n\n"
                + RISK_QUESTIONS[0]
            )
            next_state = "gather_risk"

        # --- State: Gather Risk Answers ---
        elif conversation_state == "gather_risk":
            logger.info("State: gather_risk. Recording answer and delivering next question.")
            question_idx = metadata.get("risk_question_index", 1)
            risk_answers: dict = metadata.get("risk_answers", {})

            # Validate and store user's answer
            letter = extract_single_choice(user_message)
            if letter is None:
                logger.warning("Invalid answer format. Asking the same question again.")
                response_message = (
                    "Sorry, please respond with just the letter a, b, c, or d.\n\n"
                    + RISK_QUESTIONS[question_idx - 1]
                )
                next_state = "gather_risk"
            else:
                risk_answers[str(question_idx)] = letter
                question_idx += 1

                if question_idx <= len(RISK_QUESTIONS):
                    # Continue questionnaire
                    metadata["risk_question_index"] = question_idx
                    metadata["risk_answers"] = risk_answers
                    response_message = RISK_QUESTIONS[question_idx - 1]
                    next_state = "gather_risk"
                else:
                    # Completed questionnaire
                    answers_str = ", ".join(f"{k}{v}" for k, v in risk_answers.items())
                    logger.info(f"Collected questionnaire answers: {answers_str}")
                    calculated_level = calculate_risk_level(answers_str)

                    if calculated_level:
                        derived_risk_level = calculated_level
                        metadata["derived_risk_level"] = derived_risk_level
                        logger.info(f"Derived risk level: {derived_risk_level}")
                        response_message = (
                            f"Thank you. Based on your answers, your risk tolerance profile is '{derived_risk_level}'.\n\n"
                            "Now, please provide the following details:\n1. Your age?\n2. Your approximate initial investment amount?\n3. Your investment time horizon (e.g., short-term, 5 years, long-term)?"
                        )
                        next_state = "gather_details"
                    else:
                        logger.error("Failed to calculate risk level after completing questionnaire.")
                        response_message = (
                            "Sorry, I couldn't determine your risk profile from the answers. Let's start over."
                        )
                        # Reset to initial to restart
                        next_state = "initial"

        # --- State: Gather Remaining Details ---
        elif conversation_state == "gather_details":
            logger.info("State: gather_details. Attempting to extract Age, Investment, Horizon.")
            # Attempt to extract remaining details using the AI model
            details_prompt = create_details_extraction_prompt(user_message, user_profile, derived_risk_level or "Unknown") # Pass risk level if known
            # Use the existing openai_client instance (assuming it's globally accessible or passed)
            model_response = await openai_client.generate_text(details_prompt) # Removed conversation_history argument
            logger.info(f"OpenAI response for detail extraction: {model_response}")

            # Extract the actual text portion depending on return type
            if isinstance(model_response, dict):
                model_response_text = model_response.get("text", "")
            else:
                model_response_text = str(model_response)

            # Check if the response is empty (indicating an error)
            if not model_response_text:
                logger.error("OpenAI client returned an empty response for detail extraction.")
            
            # Extract the actual text content from the response dictionary
            response_content = model_response_text
            if not response_content:
                logger.error("OpenAI client returned an empty response for detail extraction.")
            
            extracted_details = extract_json_from_response(response_content)
            logger.info(f"Extracted details: {extracted_details}")

            if extracted_details:
                 # Update user_profile with newly extracted details, handling potential nulls/types
                 if extracted_details.get("age") is not None: 
                     try: user_profile["age"] = int(extracted_details["age"]) 
                     except (ValueError, TypeError): logger.warning(f"Could not parse age '{extracted_details['age']}' as int.")
                 if extracted_details.get("initial_investment") is not None: 
                     try: user_profile["initial_investment"] = float(extracted_details["initial_investment"])
                     except (ValueError, TypeError): logger.warning(f"Could not parse initial_investment '{extracted_details['initial_investment']}' as float.")
                 if extracted_details.get("time_horizon") is not None: user_profile["time_horizon"] = str(extracted_details["time_horizon"])
                 
                 metadata["user_profile"] = user_profile # Persist updated profile
                 logger.info(f"Updated user profile after extraction: {user_profile}")

                 # Check if all necessary details are present
                 age = user_profile.get("age")
                 initial_investment = user_profile.get("initial_investment")
                 time_horizon = user_profile.get("time_horizon")

                 if age is not None and initial_investment is not None and time_horizon is not None and derived_risk_level is not None:
                     logger.info("All required details gathered. Proceeding to generation.")
                     next_state = "generate"
                     # Fall through to the 'generate' state logic immediately
                 else:
                     # Ask for missing information
                     missing_items = []
                     if age is None: missing_items.append("age")
                     if initial_investment is None: missing_items.append("initial investment amount")
                     if time_horizon is None: missing_items.append("investment time horizon")
                     # Don't ask for risk level again if it was derived
                     # if derived_risk_level is None: missing_items.append("risk tolerance (please answer questionnaire again if needed)")
                     if missing_items: # Only ask if something is actually missing
                         response_message = f"Thanks! I still need a bit more information. Could you please provide your {' and '.join(missing_items)}?"
                         next_state = "gather_details" # Stay in this state
                     else: # Should not happen if check above is correct, but as fallback
                         logger.warning("Logic error: In gather_details but no missing items detected. Moving to generate.")
                         next_state = "generate"

        # --- State: Post-Generation Chat (explain / refine) ---
        elif conversation_state in {"complete", "explain", "refine"}:
            logger.info("State: post-generation chat.")
            updated_portfolio = metadata.get("updated_portfolio")
            if not updated_portfolio:
                logger.warning("No portfolio in metadata during post-generation chat.")
                response_message = "I couldn't locate your portfolio data. Please generate a portfolio first."
                next_state = "initial"
            else:
                # Try to detect refine intent first
                refine_req = parse_refine_request(user_message)
                if refine_req:
                    ticker, change_pct = refine_req
                    logger.info(f"Refine request detected: {ticker} change {change_pct}")
                    # Build new target allocation from current holdings
                    current_alloc = {h["ticker"].upper(): h.get("percentage", 0) for h in updated_portfolio.get("holdings", [])}
                    if ticker not in current_alloc:
                        response_message = f"I couldn't find {ticker} in your current holdings. Please reference an existing ticker."
                        next_state = "complete"
                    else:
                        # Adjust and renormalize
                        current_alloc[ticker] = max(current_alloc[ticker] + change_pct, 0)
                        total = sum(current_alloc.values())
                        if total == 0:
                            response_message = "The requested change resulted in zero allocation. Please try a smaller adjustment."
                            next_state = "complete"
                        else:
                            current_alloc = {k: v/total for k, v in current_alloc.items()}
                            metadata["pending_refine"] = current_alloc
                            response_message = FinancialPrompts.get_refinement_ack_prompt(ticker, change_pct)
                            next_state = "generate"
                else:
                    # Explanation branch
                    holdings_json_str = json.dumps(updated_portfolio.get("holdings", []))
                    notes = updated_portfolio.get("notes")
                    expl_prompt = FinancialPrompts.get_allocation_explanation_prompt(user_message, holdings_json_str, notes)
                    # Get system instructions from metadata if provided by frontend
                    system_instructions = metadata.get("system_instructions")
                    model_resp = await openai_client.generate_text(
                        expl_prompt,
                        system_instruction=system_instructions,
                        max_output_tokens=4096 # Substantially increase token limit for conversational responses
                    )
                    response_message = model_resp.get("text", "") if isinstance(model_resp, dict) else str(model_resp)
                    next_state = "complete"

        # --- State: Generate Portfolio ---
        if next_state == "generate": # Check next_state not conversation_state
            logger.info("State: generate. Generating portfolio.")
            conversation_state = "generate" # Ensure state is correctly set for metadata update later

            age = user_profile.get("age")
            initial_investment = user_profile.get("initial_investment")
            time_horizon = user_profile.get("time_horizon")
            risk_tolerance = derived_risk_level # Use the level from the questionnaire

            # Defensive check - should have these by now
            if not all([isinstance(age, int), 
                        isinstance(initial_investment, (int, float)), 
                        isinstance(time_horizon, str), 
                        isinstance(risk_tolerance, str)]):
                 logger.error(f"Reached 'generate' state without all required user profile data or data types are incorrect. Profile: {user_profile}, Derived Risk: {risk_tolerance}")
                 # Revert to gathering details state
                 missing_items = []
                 if not isinstance(age, int): missing_items.append("age (as a number)")
                 if not isinstance(initial_investment, (int, float)): missing_items.append("initial investment amount (as a number)")
                 if not isinstance(time_horizon, str): missing_items.append("investment time horizon (e.g., 5 years)")
                 if not isinstance(risk_tolerance, str): missing_items.append("risk tolerance (issue detected, please restart)")
                 response_message = f"It seems I'm missing some details or they weren't understood correctly. Could you please confirm your: {', '.join(missing_items)}?"
                 next_state = "gather_details"

            else:
                # Proceed with generation only if all data is present and correct types
                # Allow override if a pending_refine allocation exists
                override_alloc = metadata.pop("pending_refine", None)
                target_allocation = override_alloc if override_alloc else get_glide_path_allocation(age, risk_tolerance)
                if not target_allocation:
                    logger.error(f"Failed to get glide path allocation for age {age} and risk {risk_tolerance}")
                    response_message = f"Sorry, I couldn't find a standard allocation for your age ({age}) and risk profile ('{risk_tolerance}'). Please check the inputs or contact support."
                    next_state = "gather_details" # Allow user to correct details maybe?
                else:
                    logger.info(f"Successfully retrieved target allocation: {target_allocation}")

                    # === Two-step generation ===
                    # Step 1: use o4-mini-high for holdings math
                    try:
                        math_client = OpenAIClient(model="o4-mini")  # high-reasoning math model
                    except Exception as e:
                        logger.error(f"Failed to init o4 client: {e}")
                        math_client = openai_client  # Fallback to default

                    holdings_prompt = FinancialPrompts.get_holdings_generation_prompt(
                        age=age,
                        risk_tolerance=risk_tolerance,
                        time_horizon=time_horizon,
                        initial_investment=initial_investment,
                        target_allocation=target_allocation
                    )

                    # First attempt with a large token budget to ensure model can finish reasoning
                    holdings_resp = await math_client.generate_text(
                        holdings_prompt,
                        temperature=0.2,
                        max_output_tokens=3000  # drastically increased cap for reasoning + JSON
                    )
                    logger.info(f"o4 holdings response: {holdings_resp}")

                    holdings_text = holdings_resp.get("text", "") if isinstance(holdings_resp, dict) else str(holdings_resp)
                    holdings_json = extract_json_from_response(holdings_text) if holdings_text else None

                    # If still failed (empty or no holdings), retry once with even larger budget
                    if (not holdings_json or "holdings" not in holdings_json) and isinstance(holdings_resp, dict):
                        logger.warning("Holdings JSON not returned; retrying with higher token budget")
                        retry_resp = await math_client.generate_text(
                            holdings_prompt,
                            temperature=0.2,
                            max_output_tokens=6000  # even larger cap on retry
                        )
                        logger.info(f"o4 holdings retry response: {retry_resp}")
                        holdings_text = retry_resp.get("text", "") if isinstance(retry_resp, dict) else str(retry_resp)
                        holdings_json = extract_json_from_response(holdings_text) if holdings_text else None

                    if not holdings_json or "holdings" not in holdings_json:
                        logger.error("Failed to get holdings JSON from o4 response.")
                        response_message = "Sorry, I couldn't generate the portfolio holdings. Please try again."
                        next_state = "generate"
                    else:
                        # Step 2: summary + notes with cheaper o3
                        summary_prompt = FinancialPrompts.get_summary_notes_prompt(json.dumps(holdings_json["holdings"]))

                        # Generate summary + notes with higher token budget
                        summary_resp = await openai_client.generate_text(
                            summary_prompt,
                            temperature=0.3,
                            max_output_tokens=2000  # larger cap for reasoning + output
                        )
                        logger.info(f"o3 summary response: {summary_resp}")

                        summary_text = summary_resp.get("text", "") if isinstance(summary_resp, dict) else str(summary_resp)
                        summary_json = extract_json_from_response(summary_text) if summary_text else None

                        # Retry once if summary failed
                        if (not summary_json or not {"summary", "notes"}.issubset(summary_json)) and isinstance(summary_resp, dict):
                            logger.warning("Summary JSON not returned; retrying with higher token budget")
                            retry_summary = await openai_client.generate_text(
                                summary_prompt,
                                temperature=0.3,
                                max_output_tokens=4000  # even larger cap for retry
                            )
                            logger.info(f"o3 summary retry response: {retry_summary}")
                            summary_text = retry_summary.get("text", "") if isinstance(retry_summary, dict) else str(retry_summary)
                            summary_json = extract_json_from_response(summary_text) if summary_text else None

                        if not summary_json or not {"summary", "notes"}.issubset(summary_json):
                            logger.error("Failed to get summary/notes JSON from o3 response.")
                            response_message = "Holdings were generated, but I couldn't create the summary. Please retry."
                            next_state = "generate"
                        else:
                            # Derive simple asset-class allocations from holdings
                            allocations: Dict[str, float] = {}
                            def _classify(t: str) -> str:
                                bond_set = {"BND", "BNDX", "VTIP"}
                                reit_set = {"VNQ", "VNQI"}
                                if t in bond_set:
                                    return "Bonds"
                                if t in reit_set:
                                    return "Real Estate"
                                return "Stocks"
                            for h in holdings_json["holdings"]:
                                cls = _classify(h["ticker"].upper())
                                allocations[cls] = allocations.get(cls, 0.0) + (h.get("percentage", 0) * 100 if h.get("percentage", 1) <= 1 else h.get("percentage", 0))
                            # Ensure allocations percentages are 0-100
                            # Make sure user_profile has safe defaults so frontend string operations don't fail
                            safe_profile: Dict[str, Any] = {**user_profile} if isinstance(user_profile, dict) else {}
                            safe_profile.setdefault("risk_tolerance", derived_risk_level)
                            safe_profile.setdefault("income", "unspecified")
                            safe_profile.setdefault("time_horizon", "unspecified")
                            safe_profile.setdefault("investment_goals", [])
                            safe_profile.setdefault("initial_investment", 0)
                            safe_profile.setdefault("monthly_contribution", 0)

                            final_json = {
                                "summary": summary_json["summary"],
                                "holdings": holdings_json["holdings"],
                                "notes": summary_json["notes"],
                                # Pass through gathered user profile for frontend display
                                "user_profile": safe_profile,
                                # Convenience: include initial investment as total value if provided
                                "total_value": safe_profile.get("initial_investment"),
                                "allocations": allocations
                            }
                            logger.info("Successfully built final portfolio JSON.")
                            updated_portfolio_data = final_json
                            metadata["updated_portfolio"] = final_json  # persist for follow-up chat
                            response_message = "Great! I've generated your personalized portfolio. Opening the allocation view now."
                            next_state = "complete"

        # If next_state remains 'generate' or 'gather_details', response_message should be set within those blocks.
        # If next_state changed due to error or completion, handle response there.

    except Exception as e:
        logger.error(f"An unexpected error occurred in process_portfolio_chat: {e}", exc_info=True)
        response_message = "An unexpected error occurred while processing your request. Please try again later."
        # Preserve state or reset on error? Let's preserve for now.
        next_state = metadata.get("conversation_state", "initial") 

    # Update metadata with the final state for the next request
    metadata["conversation_state"] = next_state

    # Prepare conversation history for the response
    # Pydantic models need dicts, not ChatMessage objects directly in list for response history
    response_history = [msg.dict() for msg in conversation_history] + [
        {"role": "user", "content": user_message},
        # Only include assistant response if one was generated (might be empty on error)
        {"role": "assistant", "content": response_message} if response_message else {}
    ]
    # Filter out empty history entries potentially caused by errors
    response_history = [entry for entry in response_history if entry]


    return ChatResponse(
        conversation_id=request.conversation_id,
        response=response_message,
        conversation_history=response_history, 
        metadata=metadata,
        updated_portfolio=updated_portfolio_data
    )

# Helper function to parse refine requests
def parse_refine_request(message: str) -> tuple[str, float] | None:
    """Detect requests like 'increase VNQ by 5%' or 'decrease BND 2%'.
    Returns (ticker, change_pct_decimal) where change_pct_decimal may be negative.
    """
    pattern = r"(increase|decrease|reduce|add|more|less)\s+([A-Za-z]{2,5})\s+(?:by\s+)?(\d+(?:\.\d+)?)\s*%?"
    m = re.search(pattern, message, re.IGNORECASE)
    if not m:
        return None
    verb, ticker, pct_str = m.groups()
    ticker = ticker.upper()
    pct = float(pct_str) / 100.0  # convert to decimal
    verb = verb.lower()
    if verb in {"decrease", "reduce", "less"}:
        pct = -pct
    # "increase", "add", "more" imply positive pct
    return ticker, pct

# --- New Endpoint for Updating Portfolio from Chat --- 
@app.post("/api/update-portfolio-from-chat", response_model=PortfolioResponse)
async def update_portfolio_from_chat(request: PortfolioUpdateRequest, api_key: str = Depends(get_api_key)):
    """
    Analyzes chat history with OpenAI to determine requested portfolio changes,
    calculates the new allocation, validates it, and returns the updated portfolio.
    """
    logger.info(f"Received request to update portfolio based on chat history. History length: {len(request.chat_history)}")
    
    current_portfolio_data = request.current_portfolio.portfolioData
    user_preferences = request.current_portfolio.userPreferences
    chat_history = request.chat_history
    
    current_allocations_dict = current_portfolio_data.allocations
    chat_history_dicts = [msg.model_dump() for msg in chat_history]
    total_value = current_portfolio_data.total_value

    # Construct prompt for OpenAI
    prompt_messages = [
        {"role": "system", "content": f"""
You are a portfolio adjustment assistant. Based on the user's chat history and their current portfolio allocation, determine the *final desired portfolio allocation* expressed as a JSON object where keys are stock tickers (uppercase strings from {list(TICKER_NAMES.keys())}) and values are percentages (numbers). 

The final allocation percentages MUST sum exactly to 100.0. 
Only include tickers present in the initial allocation OR explicitly mentioned positively by the user. 
Do NOT add commentary, just output the JSON object.

Current Allocation: {json.dumps(current_allocations_dict)}
"""},
    ]
    prompt_messages.extend(chat_history_dicts) # Add user/assistant messages
    prompt_messages.append({"role": "user", "content": "Based on our conversation, provide the final adjusted portfolio allocation as a JSON object."})

    try:
        logger.info("Calling OpenAI to get adjusted allocation...")
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini", # Or your preferred model supporting JSON mode
            messages=prompt_messages,
            temperature=0.2, # Lower temperature for more deterministic output
            response_format={"type": "json_object"}, # Request JSON output
            max_tokens=4000  # Explicitly set a higher token limit for the response
        )
        
        content = response.choices[0].message.content
        logger.info(f"OpenAI response received: {content}")
        
        if not content:
             raise HTTPException(status_code=400, detail="OpenAI returned an empty response.")

        # Parse the JSON response
        try:
            new_allocation_dict = json.loads(content)
            if not isinstance(new_allocation_dict, dict):
                 raise ValueError("Response is not a JSON object.")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse OpenAI JSON response: {e}. Content: {content}")
            raise HTTPException(status_code=500, detail="Failed to parse portfolio allocation from AI response.")

        # --- Validation --- 
        total_percentage = 0
        validated_allocation = {}
        all_tickers = list(TICKER_NAMES.keys())
        for ticker, percentage in new_allocation_dict.items():
            if not isinstance(ticker, str) or ticker.upper() not in all_tickers:
                logger.warning(f"Invalid ticker '{ticker}' in OpenAI response. Skipping.")
                continue # Skip invalid tickers
            try:
                # Attempt to convert percentage to float, handle potential errors
                perc_float = float(percentage)
                if perc_float < 0: # Percentages shouldn't be negative
                     logger.warning(f"Negative percentage '{percentage}' for ticker '{ticker}' found. Setting to 0.")
                     perc_float = 0.0 
                validated_allocation[ticker.upper()] = round(perc_float, 2) # Store uppercase, rounded
                total_percentage += perc_float
            except (ValueError, TypeError):
                logger.error(f"Invalid percentage value '{percentage}' for ticker '{ticker}' in OpenAI response.")
                raise HTTPException(status_code=400, detail=f"Invalid percentage format for ticker '{ticker}' from AI.")
        
        # Check if the sum is close to 100
        if abs(total_percentage - 100.0) > 1.0: # Allow tolerance up to 1% for rounding/LLM errors
             logger.error(f"New allocation percentages sum to {total_percentage:.2f}, not 100. Allocation: {validated_allocation}")
             raise HTTPException(status_code=400, detail=f"Proposed allocation from AI does not sum to 100% (Sum: {total_percentage:.2f}%). Please clarify your request.")
        
        # Normalize to exactly 100 if sum is slightly off but within tolerance
        if total_percentage != 0:
            factor = 100.0 / total_percentage
            final_allocation = {k: round(v * factor, 2) for k, v in validated_allocation.items()}
            # Ensure it sums to 100 after normalization due to potential rounding of the last element
            current_sum = sum(final_allocation.values())
            if abs(diff) > 0.01 and final_allocation: # If diff is noticeable and dict not empty
                 # Add difference to the largest allocation
                 largest_ticker = max(final_allocation, key=final_allocation.get)
                 final_allocation[largest_ticker] = round(final_allocation[largest_ticker] + diff, 2)
        else:
             final_allocation = {} # Handle case where total_percentage was 0

        logger.info(f"Validated and finalized allocation: {final_allocation}")
        
        # --- Update Portfolio Response --- 
        current_portfolio_data.allocations = final_allocation
        # Recalculate holdings based on the new allocation and existing total value
        current_portfolio_data.holdings = recalculate_holdings(final_allocation, total_value)
        # Potentially update other fields like analysis if needed, or add a note
        current_portfolio_data.analysis = f"Portfolio updated based on chat interaction. {current_portfolio_data.analysis if current_portfolio_data.analysis else ''}".strip()

        return PortfolioResponse(
            total_value=total_value,
            holdings=current_portfolio_data.holdings,
            allocations=current_portfolio_data.allocations,
            projections=current_portfolio_data.projections,
            recommendations=current_portfolio_data.recommendations,
            analysis=current_portfolio_data.analysis,
            user_profile=user_preferences.model_dump()
        )

    except HTTPException as http_exc: # Re-raise specific HTTP exceptions
        raise http_exc
    except Exception as e:
        logger.exception("Error updating portfolio from chat via OpenAI")
        raise HTTPException(status_code=500, detail=f"An internal error occurred while processing your request with the AI: {e}")

# --- End New Endpoint --- 

# --- Helper function to recalculate holdings --- 
def recalculate_holdings(allocations: Dict[str, float], total_value: float) -> List[Dict[str, Any]]:
    """Recalculates holdings list based on new allocations and total value."""
    new_holdings = []
    if not total_value or total_value <= 0:
        # If total value is zero or invalid, return based on allocation keys with 0 value
        return [{'ticker': ticker, 'name': TICKER_NAMES.get(ticker, 'Unknown Asset'), 'percentage': perc, 'value': 0}
                for ticker, perc in allocations.items()]

    valid_allocations = {k: v for k, v in allocations.items() if isinstance(v, (int, float)) and v > 0}

    # Normalize percentages slightly if they don't sum exactly due to rounding, but are close
    current_sum = sum(valid_allocations.values())
    if abs(current_sum - 100.0) < 0.1 and current_sum != 0: # Allow small tolerance
         factor = 100.0 / current_sum
         valid_allocations = {k: v * factor for k, v in valid_allocations.items()}

    for ticker, percentage in valid_allocations.items():
         # Ensure percentage is treated as float for calculation
         value = total_value * (float(percentage) / 100.0)
         new_holdings.append({
             'ticker': ticker,
             'name': TICKER_NAMES.get(ticker, 'Unknown Asset'),
             'value': round(value, 2),
             'percentage': round(float(percentage), 2) # Ensure percentage is float and rounded
         })
    # Ensure holdings are sorted or ordered consistently if needed
    new_holdings.sort(key=lambda x: x['percentage'], reverse=True)
    return new_holdings
# --- End Helper Function --- 

# --- New Endpoint for Wizard Submission --- 
@app.post("/api/generate-portfolio-from-wizard", tags=["Portfolio Generation"])
async def generate_portfolio_from_wizard(
    request: WizardRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Generates a portfolio directly from wizard answers, using default values
    for details not gathered by the wizard (age, investment, horizon etc.),
    but allows overriding age.
    """
    logger.info(f"=== PROCESSING WIZARD REQUEST ===")
    logger.info(f"Age={request.age} (type: {type(request.age)})")
    logger.info(f"firstName={request.firstName}, lastName={request.lastName}, birthday={request.birthday}")
    logger.info(f"Raw answers received: {request.answers}")
    logger.info(f"Answers keys: {list(request.answers.keys())}")

    # Convert answers dict {'q1': 'a', ...} to string "1a, 2c, ..."
    # Only process keys that start with 'q' and are valid question IDs
    valid_answers = {q: a for q, a in request.answers.items() if q.startswith('q') and q[1:].isdigit()}
    answers_str = ", ".join([f"{q.replace('q', '')}{a}" for q, a in valid_answers.items()])
    logger.info(f"Valid question keys found: {list(valid_answers.keys())}")
    logger.info(f"Formatted answers for risk calculation: {answers_str}")

    derived_risk_level = calculate_risk_level(answers_str)
    if not derived_risk_level:
        logger.error(f"Could not derive risk level from answers: {answers_str}")
        raise HTTPException(status_code=400, detail="Could not determine risk tolerance from provided answers.")

    logger.info(f"Derived risk level from wizard: {derived_risk_level}")

    # Map questionnaire risk level to glide path key
    glide_path_risk_key = QUESTIONNAIRE_TO_GLIDE_PATH_MAP.get(derived_risk_level)
    if not glide_path_risk_key:
         logger.error(f"Could not map derived risk level '{derived_risk_level}' to a glide path key.")
         raise HTTPException(status_code=400, detail=f"Invalid derived risk level: {derived_risk_level}")

    # Use provided age or extract from answers as fallback, or default to 35
    user_age = request.age
    logger.info(f"STEP 1: request.age = {request.age}")
    
    # Fallback: extract age from contaminated answers if not provided properly
    if user_age is None:
        logger.info(f"STEP 2: request.age is None, checking answers for age...")
        age_from_answers = request.answers.get('age')
        logger.info(f"STEP 3: Found age in answers: {age_from_answers} (type: {type(age_from_answers)})")
        
        if age_from_answers:
            try:
                user_age = int(str(age_from_answers))
                logger.info(f"FALLBACK SUCCESS: Extracted age {user_age} from contaminated answers")
            except (ValueError, TypeError) as e:
                logger.error(f"FALLBACK FAILED: Could not convert age '{age_from_answers}' to int: {e}")
    
    # Final fallback to default
    if user_age is None or user_age <= 0:
        user_age = 35
        logger.info(f"FINAL FALLBACK: Using default age 35")
    
    logger.info(f"DEBUG: Raw request.age value: {request.age}, Type: {type(request.age)}")
    if not (18 <= user_age <= 100):
         logger.warning(f"Provided age {user_age} is outside the typical range (18-100). Using default 35.")
         user_age = 35 # Reset to default if out of range

    logger.info(f"Using age: {user_age} (Provided: {request.age})")

    # Get allocations based on age and derived risk level  
    allocation_percentages = get_glide_path_allocation(user_age, derived_risk_level)
    if not allocation_percentages:
        logger.error(f"Could not find glide path allocation for age {user_age} and risk {derived_risk_level}")
        raise HTTPException(status_code=500, detail="Internal error: Could not determine base portfolio allocation.")

    logger.info(f"Found allocation for age {user_age}, risk '{derived_risk_level}': Range (33-37)")
    logger.info(f"Retrieved glide path allocation: {allocation_percentages}")

    # Format Portfolio Data (matching frontend expectations)
    EQUITY_TICKERS = {"VTI", "VUG", "VBR", "VEA", "VSS", "VWO"}
    IGNORE_KEYS = {"Equity %", "Real Assets %", "Cash %", "Bonds %"}

    default_initial_investment = 50000.0
    holdings = []
    calculated_allocations = {}
    total_value = default_initial_investment
    equity_total_pct = allocation_percentages.get('Equity %', 0.0)
    cash_pct = allocation_percentages.get('Cash %', 0.0)

    # Calculate the sum of raw equity percentages for normalization
    raw_equity_sum = sum(
        allocation_percentages.get(ticker, 0.0) 
        for ticker in EQUITY_TICKERS 
        if ticker in allocation_percentages
    )
    if raw_equity_sum <= 0:
        logger.warning(f"Sum of raw equity percentages is {raw_equity_sum}. Equity allocation will be zero.")
        raw_equity_sum = 1.0

    for ticker, raw_percentage in allocation_percentages.items():
        if ticker in IGNORE_KEYS or raw_percentage <= 0:
            continue

        final_pct = 0.0
        if ticker in EQUITY_TICKERS:
            normalized_equity_pct = raw_percentage / raw_equity_sum
            final_pct = equity_total_pct * normalized_equity_pct
        else:
            final_pct = raw_percentage

        if final_pct > 0:
            holding_value = round(total_value * final_pct, 2)
            final_pct_rounded = round(final_pct * 100, 2)
            holdings.append({
                "ticker": ticker,
                "name": TICKER_NAMES.get(ticker, ticker),
                "value": holding_value,
                "percentage": final_pct_rounded
            })
            calculated_allocations[ticker] = final_pct_rounded

    # Add Cash allocation if needed
    if cash_pct > 0:
        calculated_allocations['Cash'] = round(cash_pct * 100, 2)

    # User preferences matching frontend expectations
    user_preferences = {
        "age": user_age,
        "income": "mid-range",
        "riskTolerance": derived_risk_level,
        "investmentGoals": ["growth", "retirement"],
        "timeHorizon": "long-term",
        "initialInvestment": default_initial_investment,
        "monthlyContribution": 500.0,
        "sectorPreferences": [],
        "avoidSectors": []
    }

    # Portfolio data matching frontend expectations
    placeholder_projections = {"years": [0, 5, 10, 20], "values": [total_value] * 4}
    placeholder_recommendations = [
        {"title": "Review Allocation", "description": "This portfolio is based on standard glide paths. Further customization is recommended."}
    ]
    placeholder_analysis = f"Generated portfolio based on a '{derived_risk_level}' risk tolerance and standard glide path allocations for age {user_age}."
    
    portfolio_data = {
        "totalValue": total_value,
        "holdings": holdings,
        "allocations": calculated_allocations,
        "projections": placeholder_projections,
        "recommendations": placeholder_recommendations,
        "analysis": placeholder_analysis,
        "glidePath": allocation_percentages,
        "rationale": placeholder_analysis
    }

    # Structure final response as expected by frontend
    final_response_data = {
        "portfolioData": portfolio_data, 
        "userPreferences": user_preferences
    }

    # Save user record if personal data provided
    if request.firstName or request.lastName or request.birthday:
        risk_score, _ = calculate_risk_score_and_level(answers_str)
        user_record_data = {
            "firstName": request.firstName,
            "lastName": request.lastName,
            "birthday": request.birthday,
            "age": user_age,
            "risk_level": derived_risk_level,
            "risk_score": risk_score,
            "portfolio_allocation": allocation_percentages
        }
        user_id = save_user_record(user_record_data)
        final_response_data["user_id"] = user_id
    
    logger.info("Successfully generated portfolio structure from wizard.")
    return final_response_data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 

# --- Exception Handler for Validation Errors ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log the details of the validation error
    logger.error(f"Request validation error details: {exc.errors()}")
    try:
        # Attempt to read and log the raw request body
        raw_body = await request.body()
        logger.error(f"Failing request body for 422 error: {raw_body.decode()}")
    except Exception as e:
        logger.error(f"Could not read body from failing request during validation: {e}")
    
    # Return the default 422 response but with logged details
    # You might want to customize the response content further if needed
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )
# --- End Exception Handler ---