import os
import io
import tempfile
from uuid import uuid4
from typing import Dict, Any

from utils.processing_helpers import process_single_document_core
from noi_calculations import calculate_noi_comparisons

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from datetime import datetime

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
TEMPLATE_NAME = "report_template.html"


class _UploadedFile(io.BytesIO):
    """Simple in-memory file object that mimics the parts used by Streamlit UploadFile."""

    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


def _identify_role(filename: str) -> str:
    """Heuristic to map filename to document role."""
    name = filename.lower()
    if "budget" in name:
        return "current_month_budget"
    if "prior" in name and "year" in name:
        return "prior_year_actuals"
    if "prior" in name:
        return "prior_month_actuals"
    return "current_month_actuals"


def _role_to_internal(role: str) -> str:
    mapping = {
        "current_month_actuals": "current_month",
        "prior_month_actuals": "prior_month",
        "current_month_budget": "budget",
        "prior_year_actuals": "prior_year",
    }
    return mapping.get(role, role)


def run_noi_pipeline(temp_dir: str) -> str:
    """Run NOI pipeline on all files in a temporary directory. Returns the generated PDF path."""

    file_paths = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir)]
    consolidated: Dict[str, Any] = {}

    for path in file_paths:
        role = _identify_role(os.path.basename(path))
        internal_key = _role_to_internal(role)
        with open(path, "rb") as f:
            data = f.read()
        uploaded = _UploadedFile(data, os.path.basename(path))
        result = process_single_document_core(uploaded, role)

        if "error" in result:
            # Skip or raise depending on role criticality
            if role == "current_month_actuals":
                raise RuntimeError(f"Failed processing required file {path}: {result['error']}")
            continue

        consolidated[internal_key] = result["formatted_data"]

    if "current_month" not in consolidated:
        raise RuntimeError("Current month data missing after processing. Cannot proceed.")

    comparison_results = calculate_noi_comparisons(consolidated)

    # Build minimal context for template
    context = {
        "datetime": datetime,
        "property_name": consolidated.get("current_month", {}).get("property_name", "Property"),
        "performance_data": comparison_results.get("current", {}),
    }

    # Load template
    if os.path.exists(os.path.join(TEMPLATE_DIR, TEMPLATE_NAME)):
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
        template = env.get_template(TEMPLATE_NAME)
    else:
        env = Environment(autoescape=True)
        template = env.from_string("<h1>NOI Report – {{ property_name }}</h1><p>No template found.</p>")

    html = template.render(**context)

    report_path = os.path.join(tempfile.gettempdir(), f"noi_report_{uuid4().hex}.pdf")
    HTML(string=html).write_pdf(report_path)
    return report_path 