# mcp_server_validator.py

"""
MCP Tool Server for validation of the extracted case study metadata.
Uses Pydantic schema to ensure required fields and lengths.
"""

from pydantic import BaseModel, ValidationError, constr
from agents.mcp import MCPToolServer, tool
from pydantic import BaseModel, constr

# class CaseStudySummary(BaseModel):
#     file: str
#     summary: constr(min_length=30)
#     category_domain_tech: constr(min_length=10)
#     full_text: constr(min_length=100)
class CaseStudySummary(BaseModel):
    file: str
    summary: constr(min_length=30)  # type: ignore
    category_domain_tech: constr(min_length=10)  # type: ignore
    full_text: constr(min_length=100)  # type: ignore


class ValidatorMCPServer(MCPToolServer):
    @tool
    def validate(self, item: dict):
        """
        Validates the item dictionary against schema.
        """
        try:
            CaseStudySummary(**item)
            return {"valid": True, "detail": "Validation passed."}
        except ValidationError as e:
            return {"valid": False, "errors": e.errors()}


if __name__ == "__main__":
    ValidatorMCPServer().serve()