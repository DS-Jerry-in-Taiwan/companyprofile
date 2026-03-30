from pydantic import BaseModel, Field

class LLMOutput(BaseModel):
    title: str = Field(..., description="The title of the LLM output.")
    body_html: str = Field(..., description="The HTML content of the LLM output.")
    summary: str = Field(..., description="A summary of the LLM output.")

    class Config:
        schema_extra = {
            "example": {
                "title": "Sample Title",
                "body_html": "<p>This is a sample body.</p>",
                "summary": "This is a summary."
            }
        }
