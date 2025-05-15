from typing import Dict

class DiscussionLens:
    """
    Given a round number, returns the theme for that round.
    Rounds 1–30 are defined; rounds beyond this will raise an error.
    """

    THEMES: Dict[int, str] = {
        1:  "Technical Capabilities",
        2:  "Economic Impact",
        3:  "Geopolitical Ramifications",
        4:  "Labor Market & Skills",
        5:  "Legal & Regulatory",
        6:  "Ethical Considerations",
        7:  "Social & Cultural Change",
        8:  "Environmental Sustainability",
        9:  "Education & Training",
        10: "Digital Divide & Equity",
        11: "Industry Deep Dive",
        12: "Psychological Well-Being",
        13: "Future Scenarios (10+ yrs)",
        14: "Human Creativity & Innovation",
        15: "Security & Defense",
        16: "Global South Perspective",
        17: "Income Distribution & Wealth Inequality",
        18: "Algorithmic Transparency",
        19: "Corporate & Business Strategy",
        20: "Long-term Governance",
        21: "Public Perception & Media Narratives",
        22: "Philosophical Foundations",
        23: "Technological Adoption Curves",
        24: "Risk Management & Resilience",
        25: "Data Privacy & Surveillance",
        26: "Healthcare & Well-being",
        27: "Urbanization & Demographic Shifts",
        28: "Algorithmic Governance",
        29: "Cross-Generational Equity",
        30: "Interdisciplinary Integration",
    }

    @classmethod
    def get_theme(cls, round_number: int) -> str:
        """
        Return the theme for the given round.
        Raises ValueError if the round is out of range.
        """
        if round_number not in cls.THEMES:
            raise ValueError(f"No theme defined for round {round_number}.")
        return cls.THEMES[round_number]


# # --- Usage Example ---
# if __name__ == "__main__":
#     for rnd in range(4, 50):
#         try:
#             idx = rnd - 3
#             if idx < 1 or idx > 30:
#                 theme = "free theme."
#                 print(f"Round {idx:2d} theme is not defined. Using free theme.")
                
#                 #raise ValueError(f"Round {rnd} is out of range. {idx} is not between 1 and 30.")
#             else:
#                 print(f"Round {idx:2d}: {DiscussionLens.get_theme(idx)}")
#         except ValueError as e:
#             theme = "free theme."
#             print(f"Round {idx:2d}: {e}")