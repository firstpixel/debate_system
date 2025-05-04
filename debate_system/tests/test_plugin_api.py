from app.integration_plugin import run_plugin
import plugins.rebuttal_strength  # Ensure registration

def test_run_registered_plugin():
    result = run_plugin("RebuttalStrengthValidator", {
        "text": "However, this ignores the safety concerns."
    })
    assert result["strength"] == "high"
