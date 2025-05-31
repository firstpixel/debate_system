from typing import Dict

class DiscussionLens:
    """
    Given a round number, returns the theme for that round.
    Rounds 1–30 are defined; rounds beyond this will raise an error.
    """

    THEMES: Dict[int, str] = {
        1:  "Technical Capabilities",
        2:  "Algorithmic Transparency",
        3:  "Legal & Regulatory",
        4:  "Ethical Considerations",
        5:  "Data Privacy & Surveillance",
        6:  "Risk Management & Resilience",
        7:  "Security & Defense",
        8:  "Geopolitical Ramifications",
        9:  "Global South Perspective",
        10: "Economic Impact",
        11: "Labor Market & Skills",
        12: "Income Distribution & Wealth Inequality",
        13: "Digital Divide & Equity",
        14: "Education & Training",
        15: "Cross-Generational Equity",
        16: "Future Scenarios (10+ yrs)",
        17: "Long-term Governance",
        18: "Algorithmic Governance",
        19: "Corporate & Business Strategy",
        20: "Industry Deep Dive",
        21: "Healthcare & Well-being",
        22: "Psychological Well-Being",
        23: "Social & Cultural Change",
        24: "Human Creativity & Innovation",
        25: "Technological Adoption Curves",
        26: "Urbanization & Demographic Shifts",
        27: "Environmental Sustainability",
        28: "Interdisciplinary Integration",
        29: "Public Perception & Media Narratives",
        30: "Wrap-up & Synthesis"      # or revisit “Technical Capabilities” if you prefer a perfect loop
    }
    
    THEMES_SOCIETY_TECH: Dict[int, str] = {
        1:  "Technical Capabilities & Limitations",
        2:  "Algorithmic Transparency & Accountability",
        3:  "Legal & Regulatory Frameworks",
        4:  "Ethical Considerations",
        5:  "Data Privacy & Surveillance",
        6:  "Risk Management & Resilience",
        7:  "Security & Defense",
        8:  "Geopolitics & Global Inclusion",
        9:  "Economic Impact & Inequality",
        10: "Labor, Skills & Education",
        11: "Digital Divide & Equity",
        12: "Health, Well-being & Society",
        13: "Environmental Sustainability",
        14: "Public Perception & Media Narratives",
        15: "Future Scenarios & Foresight"
    }
    
    THEMES_SCIENCE: Dict[int, str] = {
        1:  "Scientific Problem Definition",
        2:  "Methods, Experimentation & Rigor",
        3:  "Evidence & Data Quality",
        4:  "Statistical Analysis & Interpretation",
        5:  "Replicability & Peer Review",
        6:  "Technological Innovation",
        7:  "Ethics in Research",
        8:  "Interdisciplinary Integration",
        9:  "Environmental & Societal Impact",
        10: "Funding & Science Policy",
        11: "Open Science & Communication",
        12: "Equity & Access in Research",
        13: "Failures, Null Results & Learning",
        14: "Public Trust & Misinformation",
        15: "Future Directions & Emerging Fields"
    }
    
    THEMES_PHILOSOPHY: Dict[int, str] = {
        1:  "Definitions & Core Concepts",
        2:  "Historical & Contextual Perspectives",
        3:  "Ontology & Metaphysics",
        4:  "Epistemology & Ways of Knowing",
        5:  "Ethics & Moral Philosophy",
        6:  "Aesthetics & Artistic Value",
        7:  "Meaning, Purpose & Flourishing",
        8:  "Identity, Self & Subjectivity",
        9:  "Society, Culture & Ritual",
        10: "Language & Communication",
        11: "Power, Justice & Rights",
        12: "Religion, Faith & Spirituality",
        13: "Creativity, Innovation & Expression",
        14: "Technology, Science & Humanity",
        15: "Critique & Meta-Reflection"
    }


    @classmethod
    def get_theme(cls, round_number: int) -> str:
        """
        Return the theme for the given round.
        """
        if round_number not in cls.THEMES_SOCIETY_TECH:
            return f"Free Round, no lens defined for round {round_number}."
        return cls.THEMES_SOCIETY_TECH[round_number]


# # --- Usage Example ---
# if __name__ == "__main__":
#     for rnd in range(4, 50):
#         try:
#             idx = rnd - 3
#             if idx < 1 or idx > 30:
#                 theme = "free theme."
#                 print(f"Round {idx:2d} theme is not defined. Using free theme.")
#
#                 #raise ValueError(f"Round {rnd} is out of range. {idx} is not between 1 and 30.")
#             else:
#                 print(f"Round {idx:2d}: {DiscussionLens.get_theme(idx)}")
#         except ValueError as e:
#             theme = "free theme."
#             print(f"Round {idx:2d}: {e}")