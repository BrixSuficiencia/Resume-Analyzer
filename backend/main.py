from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
import pdfplumber
import re
import io

app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the Hugging Face model for zero-shot classification
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Role-based requirement templates
ROLE_TEMPLATES = {
    "teacher": ["classroom management", "curriculum development", "lesson planning", "teaching experience", "student assessment"],
    "admin": ["event management", "office administration", "budget management", "staff coordination", "communication skills"],
    "it_support": ["network troubleshooting", "hardware maintenance", "software installation", "technical support", "IT certifications"],
}

@app.post("/analyze-resume/")
async def analyze_resume(
    file: UploadFile = File(None), 
    requirements: str = Form(...), 
    role: str = Form("general")
):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided.")
    
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF.")
    
    content = await file.read()
    text = extract_text_from_pdf(content)
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="Failed to extract text from the uploaded PDF.")
    
    # Use role-specific requirements
    role_requirements = ROLE_TEMPLATES.get(role.lower(), [])
    all_requirements = list(set(requirements.split(",") + role_requirements))  # Avoid duplicate labels
    combined_requirements = ", ".join(all_requirements)

    # Filter relevant text and calculate AI-based score
    filtered_text = filter_relevant_text(text, combined_requirements)
    scores, best_match = calculate_score_with_ai(text, combined_requirements)
    
    return {
        "filename": file.filename,
        "role": role,
        "best_match": best_match,
        "scores": scores,
        "extracted_text": text[:500] + "...",
        "filtered_text": filtered_text[:500] + "..." if filtered_text else "No relevant text found."
    }

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from a PDF file."""
    try:
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            return "\n".join([page.extract_text() or "" for page in pdf.pages])
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def filter_relevant_text(resume_text: str, requirements_text: str) -> str:
    """Filter sentences from the resume that match the requirements."""
    requirements_words = set(re.findall(r'\b\w+\b', requirements_text.lower()))
    sentences = re.split(r'[.!?]\s+', resume_text)  # Split text into sentences

    relevant_sentences = [
        sentence for sentence in sentences
        if requirements_words & set(re.findall(r'\b\w+\b', sentence.lower()))
    ]
    
    return ". ".join(relevant_sentences)

def calculate_score_with_ai(resume_text: str, requirements_text: str):
    """Use Hugging Face's zero-shot classification to calculate a compatibility score."""
    labels = list(set(label.strip().lower() for label in requirements_text.split(",") if label.strip()))  # Normalize labels
    
    if not labels:
        return {}, "No valid requirements provided."
    
    result = classifier(resume_text, labels, multi_class=True)
    scores = {label: round(score * 100, 2) for label, score in zip(result["labels"], result["scores"])}
    best_match = max(scores, key=scores.get)
    
    return scores, best_match
