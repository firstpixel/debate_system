from app.integration_plugin import register_plugin

@register_plugin("RebuttalStrengthValidator")
class RebuttalStrengthValidator:
    def run(self, input_data):
        text = input_data["text"]
        if "however" in text.lower() or "but" in text.lower():
            return {"strength": "high"}
        return {"strength": "low"}
