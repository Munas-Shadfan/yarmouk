"""
Comprehensive URL knowledge base for Yarmouk University.
Built from live crawl of www.yu.edu.jo and all subdomains (March 2026).
Helps the agent route questions to the right page/document without searching.
"""

# ─────────────────────────────────────────────────────────────────────────────
# DIRECT KNOWN PDF URLS (confirmed to exist on the live site)
# ─────────────────────────────────────────────────────────────────────────────
KNOWN_PDFS: dict[str, dict] = {
    "majors": {
        "url": "https://admreg.yu.edu.jo/images/docs/majors.pdf",
        "desc": "Full list of majors / academic programs offered at Yarmouk University",
        "keywords": ["majors", "programs", "specializations", "تخصصات", "برامج"],
    },
    "public_universities_rules": {
        "url": "https://admreg.yu.edu.jo/images/docs/PublicUniversitiesRules.pdf",
        "desc": "Jordanian public universities regulations / by-laws",
        "keywords": ["rules", "regulations", "by-laws", "أنظمة", "قوانين", "لوائح"],
    },
    "bridging_programs": {
        "url": "https://admreg.yu.edu.jo/images/docs/Bridgingpri.pdf",
        "desc": "Bridging / preparatory programs admission requirements",
        "keywords": ["bridging", "preparatory", "bridge", "تجسيري"],
    },
    "staff_phones": {
        "url": "https://admreg.yu.edu.jo/images/docs/phone.pdf",
        "desc": "Admission & Registration staff phone numbers and extensions",
        "keywords": ["phone", "contact", "extension", "هاتف", "رقم", "تواصل"],
    },
    "newsletter_2024": {
        "url": "https://www.yu.edu.jo/images/docs/YU_Newsletter_2024.pdf",
        "desc": "Yarmouk University Newsletter 2024",
        "keywords": ["newsletter", "نشرة", "2024"],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# KEY WEBSITE PAGES (HTML — use web_page_tool on these)
# ─────────────────────────────────────────────────────────────────────────────
KEY_PAGES: dict[str, dict] = {
    # ── Admission & Registration (admreg.yu.edu.jo) ─────────────────────────
    "admreg_home": {
        "url": "https://admreg.yu.edu.jo/",
        "desc": "Admission & Registration home — links to all student services and PDFs",
        "keywords": ["registration", "admission", "تسجيل", "قبول"],
    },
    "academic_calendar": {
        "url": "https://admreg.yu.edu.jo/index.php/unical",
        "desc": "Academic calendar index — links to current and past year calendars",
        "keywords": ["calendar", "dates", "semester", "تقويم", "مواعيد", "فصل"],
    },
    "academic_calendar_2025_2026": {
        "url": "https://admreg.yu.edu.jo/index.php/unical/1450-2026-2025",
        "desc": "Academic calendar for the year 2025/2026 (current year)",
        "keywords": ["2025", "2026", "calendar", "dates", "تقويم"],
    },
    "schedule_dept": {
        "url": "https://admreg.yu.edu.jo/index.php/schedule",
        "desc": "Timetable department — course schedule and exam scheduling info",
        "keywords": ["schedule", "timetable", "جدول", "امتحان"],
    },
    "graduation": {
        "url": "https://admreg.yu.edu.jo/index.php/graduate",
        "desc": "Graduation procedures and requirements",
        "keywords": ["graduation", "graduate", "تخرج"],
    },
    "student_data_check": {
        "url": "https://admreg.yu.edu.jo/index.php/Checkingdata",
        "desc": "Student data verification service",
        "keywords": ["data", "verification", "check", "بيانات"],
    },
    "diwan": {
        "url": "https://admreg.yu.edu.jo/index.php/Diwan",
        "desc": "Diwan / records department",
        "keywords": ["diwan", "ديوان", "records", "wathiqa"],
    },
    "medicine_pharmacy_engineering": {
        "url": "https://admreg.yu.edu.jo/index.php/Medphareng",
        "desc": "Medicine, Pharmacy & Engineering college registration info",
        "keywords": ["medicine", "pharmacy", "engineering", "طب", "صيدلة", "هندسة"],
    },
    "law_economics": {
        "url": "https://admreg.yu.edu.jo/index.php/LawEconomics",
        "desc": "Law & Economics college registration info",
        "keywords": ["law", "economics", "حقوق", "اقتصاد"],
    },
    "it_sciences": {
        "url": "https://admreg.yu.edu.jo/index.php/itSciences",
        "desc": "IT & Sciences college registration info",
        "keywords": ["it", "computer", "science", "حاسوب", "علوم", "تقنية"],
    },
    "arts_media": {
        "url": "https://admreg.yu.edu.jo/index.php/Artsmediamonumentstourism",
        "desc": "Arts, Media, Archaeology & Tourism college registration info",
        "keywords": ["arts", "media", "tourism", "archaeology", "آداب", "إعلام", "سياحة"],
    },
    "education_sports": {
        "url": "https://admreg.yu.edu.jo/index.php/Educationsportslaw",
        "desc": "Education, Sports & Law college registration info",
        "keywords": ["education", "sports", "تربية", "رياضة"],
    },
    "admreg_news": {
        "url": "https://admreg.yu.edu.jo/index.php/information",
        "desc": "Latest news and announcements from Admission & Registration",
        "keywords": ["news", "announcements", "اعلانات", "اخبار"],
    },

    # ── Main University Site (www.yu.edu.jo) ────────────────────────────────
    "main_home": {
        "url": "https://www.yu.edu.jo/",
        "desc": "Main university homepage — news, events, quick links",
        "keywords": ["home", "yarmouk", "university", "جامعة", "اليرموك"],
    },
    "student_portal": {
        "url": "https://www.yu.edu.jo/index.php/ar/studentar",
        "desc": "Student portal — links to SIS, elearning, calendar",
        "keywords": ["student", "portal", "طالب", "خدمات"],
    },
    "employee_portal": {
        "url": "https://www.yu.edu.jo/index.php/ar/employeesar",
        "desc": "Employee/staff portal — HR services, elearning, payroll",
        "keywords": ["employee", "staff", "موظف", "عاملين"],
    },
    "news_events": {
        "url": "https://www.yu.edu.jo/index.php/newsevents/yu-news-ar",
        "desc": "All university news and events",
        "keywords": ["news", "events", "اخبار", "احداث"],
    },
    "announcements": {
        "url": "https://www.yu.edu.jo/index.php/ann-ar",
        "desc": "Official university announcements",
        "keywords": ["announcement", "notice", "اعلان"],
    },
    "laws_regulations": {
        "url": "http://law.yu.edu.jo/",
        "desc": "University laws, regulations and bylaws",
        "keywords": ["law", "regulation", "bylaw", "نظام", "قانون", "تعليمات"],
    },
    "student_guide": {
        "url": "https://www.yu.edu.jo/studentguide/",
        "desc": "Official student guide / handbook",
        "keywords": ["guide", "handbook", "دليل", "طالب"],
    },
    "reg_time": {
        "url": "https://www.yu.edu.jo/index.php/regtime",
        "desc": "Registration schedule / timing",
        "keywords": ["registration time", "timing", "وقت التسجيل"],
    },

    # ── Library ─────────────────────────────────────────────────────────────
    "library": {
        "url": "https://library.yu.edu.jo/",
        "desc": "Hussein bin Talal University Library — resources, databases, hours",
        "keywords": ["library", "books", "databases", "مكتبة", "كتب"],
    },

    # ── Queen Rania Center ───────────────────────────────────────────────────
    "qrc_home": {
        "url": "https://qrc.yu.edu.jo/",
        "desc": "Queen Rania Center for Jordanian Studies — training, research",
        "keywords": ["qrc", "queen rania", "center", "رانيا", "مركز"],
    },
    "qrc_training": {
        "url": "https://qrc.yu.edu.jo/index.php/training/training-course-ar",
        "desc": "Training courses at QRC",
        "keywords": ["training", "courses", "دورات", "تدريب"],
    },
    "qrc_professional_diploma": {
        "url": "https://qrc.yu.edu.jo/index.php/training/professional-diploma-study-plans",
        "desc": "Professional diploma programs at QRC",
        "keywords": ["diploma", "professional", "دبلوم", "مهني"],
    },

    # ── HR ───────────────────────────────────────────────────────────────────
    "hr_jobs": {
        "url": "https://hr.yu.edu.jo/job/userpage/AdvertisementPage.aspx",
        "desc": "Job vacancies and open positions",
        "keywords": ["jobs", "vacancies", "employment", "وظائف", "تعيين"],
    },
    "hr_scholarships": {
        "url": "https://hr.yu.edu.jo/scholarships/UserPage/AdvertisementPage.aspx",
        "desc": "Scholarship and study grant announcements",
        "keywords": ["scholarship", "grant", "study abroad", "بعثة", "منحة"],
    },

    # ── Accreditation ────────────────────────────────────────────────────────
    "accreditation": {
        "url": "https://aqac.yu.edu.jo/",
        "desc": "Accreditation & Quality Assurance Center",
        "keywords": ["accreditation", "quality", "اعتماد", "جودة"],
    },

    # ── Tenders ─────────────────────────────────────────────────────────────
    "tenders": {
        "url": "https://tendering.yu.edu.jo/Tendering/",
        "desc": "University tenders and procurement",
        "keywords": ["tender", "procurement", "bid", "مناقصة"],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# ROUTING: match a user query to the best starting pages/PDFs
# ─────────────────────────────────────────────────────────────────────────────
def route_query(query: str) -> dict[str, list[str]]:
    """
    Given a free-text user query, return suggested pages and PDFs to check.
    Returns: {"pages": [...urls], "pdfs": [...urls]}
    Used internally by the agent to decide where to look first.
    """
    q = query.lower()
    pages, pdfs = [], []

    # Academic calendar / dates / deadlines
    if any(w in q for w in ["calendar", "date", "deadline", "semester", "schedule",
                             "تقويم", "مواعيد", "جدول", "فصل", "تسجيل وقت"]):
        pages += [KEY_PAGES["academic_calendar"]["url"],
                  KEY_PAGES["academic_calendar_2025_2026"]["url"]]

    # Registration
    if any(w in q for w in ["register", "registration", "enroll", "تسجيل", "قبول"]):
        pages += [KEY_PAGES["admreg_home"]["url"], KEY_PAGES["reg_time"]["url"]]

    # Majors / programs
    if any(w in q for w in ["major", "program", "specializ", "تخصص", "برنامج"]):
        pdfs += [KNOWN_PDFS["majors"]["url"]]

    # Graduation
    if any(w in q for w in ["graduat", "تخرج", "degree", "شهادة"]):
        pages += [KEY_PAGES["graduation"]["url"]]

    # Rules / regulations / laws
    if any(w in q for w in ["rule", "regulation", "law", "bylaw", "نظام", "قانون",
                             "تعليمات", "لوائح"]):
        pages += [KEY_PAGES["laws_regulations"]["url"]]
        pdfs  += [KNOWN_PDFS["public_universities_rules"]["url"]]

    # Jobs / scholarships
    if any(w in q for w in ["job", "vacanc", "hire", "وظيف", "تعيين"]):
        pages += [KEY_PAGES["hr_jobs"]["url"]]
    if any(w in q for w in ["scholarship", "grant", "بعثة", "منحة"]):
        pages += [KEY_PAGES["hr_scholarships"]["url"]]

    # Library
    if any(w in q for w in ["library", "book", "database", "مكتبة", "كتاب"]):
        pages += [KEY_PAGES["library"]["url"]]

    # Training / diploma (QRC)
    if any(w in q for w in ["training", "course", "diploma", "دورة", "دبلوم", "تدريب"]):
        pages += [KEY_PAGES["qrc_training"]["url"],
                  KEY_PAGES["qrc_professional_diploma"]["url"]]

    # News / announcements
    if any(w in q for w in ["news", "announcement", "event", "اخبار", "اعلان", "فعالية"]):
        pages += [KEY_PAGES["news_events"]["url"], KEY_PAGES["announcements"]["url"]]

    # Contact / phone / staff
    if any(w in q for w in ["phone", "contact", "email", "staff", "هاتف", "بريد"]):
        pdfs  += [KNOWN_PDFS["staff_phones"]["url"]]

    # College-specific
    if any(w in q for w in ["computer", "it", "حاسوب", "تقنية", "معلومات"]):
        pages += [KEY_PAGES["it_sciences"]["url"]]
    if any(w in q for w in ["medicine", "pharmacy", "engineering", "طب", "صيدلة", "هندسة"]):
        pages += [KEY_PAGES["medicine_pharmacy_engineering"]["url"]]
    if any(w in q for w in ["law", "economics", "حقوق", "اقتصاد"]):
        pages += [KEY_PAGES["law_economics"]["url"]]
    if any(w in q for w in ["arts", "media", "tourism", "آداب", "إعلام", "سياحة"]):
        pages += [KEY_PAGES["arts_media"]["url"]]
    if any(w in q for w in ["education", "sports", "تربية", "رياضة"]):
        pages += [KEY_PAGES["education_sports"]["url"]]

    # Fallback: always suggest admreg home as it has student service links
    if not pages and not pdfs:
        pages = [KEY_PAGES["admreg_home"]["url"], KEY_PAGES["main_home"]["url"]]

    # Deduplicate
    return {"pages": list(dict.fromkeys(pages)), "pdfs": list(dict.fromkeys(pdfs))}
