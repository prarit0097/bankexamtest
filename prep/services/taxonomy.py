from django.utils.text import slugify

from prep.models import Exam, Section, Topic


MAJOR_BANKING_TAXONOMY = [
    {
        "code": "IBPS-PO",
        "name": "IBPS Probationary Officer",
        "sections": {
            "Quantitative Aptitude": ["Simplification", "Data Interpretation", "Arithmetic"],
            "Reasoning Ability": ["Puzzles", "Seating Arrangement", "Syllogism"],
            "English Language": ["Reading Comprehension", "Cloze Test", "Error Detection"],
            "Banking Awareness": ["Current Affairs", "Static Banking GK", "Financial Awareness"],
        },
    },
    {
        "code": "IBPS-CLERK",
        "name": "IBPS Clerk",
        "sections": {
            "Quantitative Aptitude": ["Simplification", "Number Series", "Arithmetic"],
            "Reasoning Ability": ["Puzzles", "Coding-Decoding", "Inequality"],
            "English Language": ["Reading Comprehension", "Para Jumbles", "Vocabulary"],
            "Banking Awareness": ["Current Affairs", "Static Banking GK", "Budget and Economy"],
        },
    },
    {
        "code": "SBI-PO",
        "name": "SBI Probationary Officer",
        "sections": {
            "Quantitative Aptitude": ["Data Interpretation", "Arithmetic", "Quadratic Equations"],
            "Reasoning Ability": ["Puzzles", "Critical Reasoning", "Input-Output"],
            "English Language": ["Reading Comprehension", "Cloze Test", "Word Usage"],
            "Banking Awareness": ["Current Affairs", "Banking Regulation", "Monetary Policy"],
        },
    },
    {
        "code": "SBI-CLERK",
        "name": "SBI Clerk",
        "sections": {
            "Quantitative Aptitude": ["Simplification", "Arithmetic", "Data Sufficiency"],
            "Reasoning Ability": ["Puzzles", "Blood Relations", "Direction Sense"],
            "English Language": ["Grammar", "Reading Comprehension", "Fill in the Blanks"],
            "Banking Awareness": ["Current Affairs", "Banking Basics", "Financial Institutions"],
        },
    },
    {
        "code": "RBI-ASST",
        "name": "RBI Assistant",
        "sections": {
            "Quantitative Aptitude": ["Arithmetic", "Data Interpretation", "Mensuration"],
            "Reasoning Ability": ["Puzzles", "Seating Arrangement", "Syllogism"],
            "English Language": ["Reading Comprehension", "Sentence Improvement", "Vocabulary"],
            "General Awareness": ["Current Affairs", "RBI Functions", "Indian Economy"],
        },
    },
    {
        "code": "NABARD-A",
        "name": "NABARD Grade A",
        "sections": {
            "Quantitative Aptitude": ["Data Interpretation", "Arithmetic", "Approximation"],
            "Reasoning Ability": ["Puzzles", "Logical Reasoning", "Coding-Decoding"],
            "English Language": ["Reading Comprehension", "Essay", "Grammar"],
            "General Awareness": ["Agriculture Awareness", "Rural Economy", "Current Affairs"],
        },
    },
]


_taxonomy_seeded = False


def reset_taxonomy_cache():
    global _taxonomy_seeded
    _taxonomy_seeded = False


def ensure_default_taxonomy():
    global _taxonomy_seeded
    if _taxonomy_seeded:
        return
    if Exam.objects.exists():
        _taxonomy_seeded = True
        return

    for exam_index, exam_data in enumerate(MAJOR_BANKING_TAXONOMY, start=1):
        exam = Exam.objects.create(
            code=exam_data["code"],
            name=exam_data["name"],
            description=f"{exam_data['name']} preparation track",
            is_active=True,
        )
        for section_index, (section_name, topics) in enumerate(exam_data["sections"].items(), start=1):
            section = Section.objects.create(
                exam=exam,
                name=section_name,
                slug=slugify(section_name),
                weightage_percent=25.0,
                display_order=section_index,
            )
            for topic_name in topics:
                Topic.objects.create(
                    section=section,
                    name=topic_name,
                    slug=slugify(topic_name),
                    is_high_priority=topic_name in topics[:2],
                    description=f"{topic_name} practice for {exam.name}",
                )
    _taxonomy_seeded = True
