from PyPDF2 import PdfReader
def enhance_script(script):

    enhanced = f"""
    ==============================
    🤖 NeuroLMS AI Instructor Mode
    ==============================

    📘 Teaching Introduction:
    Welcome learners!

    🎯 Today's Topic:
    {script}

    🧠 Structured Breakdown:
    1. Introduction to concept
    2. Core principles explained clearly
    3. Real-world compliance scenario
    4. Summary and reinforcement

    📌 Key Takeaway:
    Understanding compliance reduces organizational risk.

    ==============================
    End of AI Generated Teaching
    ==============================
    """

    return enhanced


def summarize_pdf(file_path):

    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text

    # Mock AI summary
    summary = f"""
    ==============================
    🤖 NeuroLMS AI Document Analyzer
    ==============================

    📘 Summary:
    {text[:500]}...

    📝 Auto Generated Quiz:
    1. What is the main topic of this document?
    2. Why is compliance important?
    3. What are key risks discussed?
    4. How can violations be prevented?
    5. What is the final takeaway?

    ==============================
    """

    return summary