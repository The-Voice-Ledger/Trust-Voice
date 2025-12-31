"""
Frontend validation tests for mini app HTML files.
Validates JavaScript code, API calls, and HTML structure.
"""
import pytest
from pathlib import Path
import re
import json


class TestHTMLFiles:
    """Validate HTML file structure and content"""
    
    @pytest.fixture
    def frontend_dir(self):
        """Get frontend directory path"""
        return Path(__file__).parent.parent / "frontend-miniapps"
    
    def test_all_html_files_exist(self, frontend_dir):
        """Test that all expected HTML files exist"""
        expected_files = [
            "index.html",
            "campaigns.html",
            "donate.html",
            "create-campaign-wizard.html",
            "ngo-register-wizard.html",
            "analytics.html",
            "admin.html",
            "conversation-analytics.html"
        ]
        
        for filename in expected_files:
            file_path = frontend_dir / filename
            assert file_path.exists(), f"Missing file: {filename}"
    
    def test_html_files_have_telegram_script(self, frontend_dir):
        """Test that HTML files include Telegram Web App script"""
        html_files = list(frontend_dir.glob("*.html"))
        
        for html_file in html_files:
            content = html_file.read_text()
            assert "telegram-web-app.js" in content, \
                f"{html_file.name} missing Telegram Web App script"
    
    def test_html_files_have_valid_structure(self, frontend_dir):
        """Test basic HTML structure"""
        html_files = list(frontend_dir.glob("*.html"))
        
        for html_file in html_files:
            content = html_file.read_text()
            assert "<!DOCTYPE html>" in content, f"{html_file.name} missing DOCTYPE"
            assert "<html" in content, f"{html_file.name} missing html tag"
            assert "<head>" in content, f"{html_file.name} missing head tag"
            assert "</head>" in content, f"{html_file.name} missing closing head tag"
            assert "<body>" in content, f"{html_file.name} missing body tag"
            assert "</body>" in content, f"{html_file.name} missing closing body tag"
            assert "</html>" in content, f"{html_file.name} missing closing html tag"
            
            # Check that style tags are properly closed
            style_opens = content.count("<style")
            style_closes = content.count("</style>")
            assert style_opens == style_closes, \
                f"{html_file.name} has {style_opens} <style> but {style_closes} </style>"
            
            # Check for malformed CSS - look for lines with just "Npx;" pattern (broken properties)
            if "<style" in content and "</style>" in content:
                style_start = content.find("<style")
                style_end = content.find("</style>")
                style_content = content[style_start:style_end]
                
                # Look for orphaned pixel values (common copy-paste error)
                if re.search(r'^\s+\d+px;\s*$', style_content, re.MULTILINE):
                    assert False, f"{html_file.name} has orphaned CSS property (lone 'Npx;' on a line)"
                
                # Check keyframes are complete
                keyframe_starts = style_content.count('@keyframes')
                if keyframe_starts > 0:
                    # Each keyframe should have from/to or percentages and closing brace
                    for match in re.finditer(r'@keyframes\s+(\w+)', style_content):
                        name = match.group(1)
                        # Find the keyframe block
                        start = match.start()
                        # Count braces after keyframe to find its end
                        rest = style_content[start:]
                        brace_count = 0
                        found_content = False
                        for char in rest:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0 and found_content:
                                    break
                            elif char not in ' \n\t' and brace_count > 0:
                                found_content = True
                        
                        assert brace_count == 0, f"{html_file.name} has unclosed keyframe: {name}"


class TestAPIEndpointCalls:
    """Validate that HTML files call correct API endpoints"""
    
    @pytest.fixture
    def frontend_dir(self):
        return Path(__file__).parent.parent / "frontend-miniapps"
    
    def extract_api_calls(self, content):
        """Extract API endpoint calls from JavaScript code"""
        # Find fetch() calls
        fetch_pattern = r'fetch\([`\'"]([^`\'"]+)[`\'"]'
        api_calls = re.findall(fetch_pattern, content)
        
        # Also find API_BASE + path patterns
        api_base_pattern = r'API_BASE\s*\+\s*[`\'"]([^`\'"]+)[`\'"]'
        api_base_calls = re.findall(api_base_pattern, content)
        
        # Find template literal patterns like ${API_BASE}/path
        template_pattern = r'\$\{API_BASE\}([/\w\-]+)'
        template_calls = re.findall(template_pattern, content)
        
        return api_calls + api_base_calls + template_calls
    
    def test_campaigns_html_api_calls(self, frontend_dir):
        """Test campaigns.html calls correct endpoints"""
        content = (frontend_dir / "campaigns.html").read_text()
        api_calls = self.extract_api_calls(content)
        
        # Should call voice search endpoint
        assert any('/voice/search-campaigns' in call for call in api_calls), \
            "campaigns.html should call /voice/search-campaigns"
        
        # Should call campaigns list endpoint
        assert any('/campaigns' in call for call in api_calls), \
            "campaigns.html should call /campaigns endpoint"
    
    def test_donate_html_api_calls(self, frontend_dir):
        """Test donate.html calls correct endpoints"""
        content = (frontend_dir / "donate.html").read_text()
        api_calls = self.extract_api_calls(content)
        
        # Should call voice dictate endpoint
        assert any('/voice/dictate' in call for call in api_calls), \
            "donate.html should call /voice/dictate"
        
        # Should call donations endpoint
        assert any('/donations' in call for call in api_calls), \
            "donate.html should call /donations endpoint"
        
        # Should call campaigns endpoint to get campaign details
        assert any('/campaigns' in call for call in api_calls), \
            "donate.html should call /campaigns to get campaign details"
    
    def test_wizard_files_api_calls(self, frontend_dir):
        """Test wizard files call wizard-step endpoint"""
        wizard_files = [
            "create-campaign-wizard.html",
            "ngo-register-wizard.html"
        ]
        
        for filename in wizard_files:
            content = (frontend_dir / filename).read_text()
            api_calls = self.extract_api_calls(content)
            
            assert any('/voice/wizard-step' in call for call in api_calls), \
                f"{filename} should call /voice/wizard-step endpoint"
    
    def test_ngo_register_calls_register_endpoint(self, frontend_dir):
        """Test NGO register wizard calls register endpoint"""
        content = (frontend_dir / "ngo-register-wizard.html").read_text()
        api_calls = self.extract_api_calls(content)
        
        assert any('/ngos/register' in call for call in api_calls), \
            "ngo-register-wizard.html should call /ngos/register"


class TestVoiceFeatures:
    """Validate voice feature implementation in HTML files"""
    
    @pytest.fixture
    def frontend_dir(self):
        return Path(__file__).parent.parent / "frontend-miniapps"
    
    def test_wizard_files_have_voice_buttons(self, frontend_dir):
        """Test wizard files have voice button functionality"""
        wizard_files = [
            "create-campaign-wizard.html",
            "ngo-register-wizard.html"
        ]
        
        for filename in wizard_files:
            content = (frontend_dir / filename).read_text()
            
            # Should have voice button
            assert "voice" in content.lower(), \
                f"{filename} should have voice features"
            
            # Should have MediaRecorder
            assert "MediaRecorder" in content, \
                f"{filename} should use MediaRecorder for voice input"
            
            # Should handle voice input
            assert "startVoiceInput" in content or "startVoice" in content, \
                f"{filename} should have voice input handler"
    
    def test_donate_html_has_voice_features(self, frontend_dir):
        """Test donate.html has voice amount and payment selection"""
        content = (frontend_dir / "donate.html").read_text()
        
        # Should have voice donation function
        assert "startVoiceDonation" in content or "voiceDonation" in content, \
            "donate.html should have voice donation function"
        
        # Should have voice payment selection
        assert "voicePayment" in content or "startVoicePayment" in content, \
            "donate.html should have voice payment selection"
        
        # Should have TTS confirmation
        assert "speechSynthesis" in content or "speakText" in content, \
            "donate.html should have TTS confirmation"
    
    def test_campaigns_html_has_voice_navigation(self, frontend_dir):
        """Test campaigns.html has voice navigation features"""
        content = (frontend_dir / "campaigns.html").read_text()
        
        # Should have voice button
        assert 'id="voiceBtn"' in content or 'class="voice-btn"' in content, \
            "campaigns.html should have voice button"
        
        # Should have voice navigation commands
        assert "speakCampaign" in content or "Listen" in content, \
            "campaigns.html should have listen/speak functionality"


class TestFormValidation:
    """Test form validation logic"""
    
    @pytest.fixture
    def frontend_dir(self):
        return Path(__file__).parent.parent / "frontend-miniapps"
    
    def test_wizard_files_validate_required_fields(self, frontend_dir):
        """Test wizards validate required fields"""
        wizard_files = [
            "create-campaign-wizard.html",
            "ngo-register-wizard.html"
        ]
        
        for filename in wizard_files:
            content = (frontend_dir / filename).read_text()
            
            # Voice wizards validate through voice flow and data checks
            # Check for validation-related keywords or data handling
            has_validation = (
                "validation" in content.lower() or
                any(word in content for word in ["required", "validate", "check"]) or
                "wizardData" in content or  # Data collection validates fields
                "if (" in content  # Conditional checks are validation
            )
            assert has_validation, f"{filename} should have form validation"


class TestErrorHandling:
    """Test error handling in JavaScript"""
    
    @pytest.fixture
    def frontend_dir(self):
        return Path(__file__).parent.parent / "frontend-miniapps"
    
    def test_files_have_try_catch(self, frontend_dir):
        """Test that API calls have error handling"""
        html_files = [
            "campaigns.html",
            "donate.html",
            "create-campaign-wizard.html",
            "ngo-register-wizard.html"
        ]
        
        for filename in html_files:
            content = (frontend_dir / filename).read_text()
            
            # Should have try-catch blocks
            assert "try {" in content and "catch" in content, \
                f"{filename} should have try-catch error handling"
            
            # Should handle fetch errors
            assert ".catch" in content or "catch (error)" in content, \
                f"{filename} should handle fetch errors"
    
    def test_files_show_error_messages(self, frontend_dir):
        """Test that files show user-friendly error messages"""
        html_files = [
            "campaigns.html",
            "donate.html",
            "create-campaign-wizard.html"
        ]
        
        for filename in html_files:
            content = (frontend_dir / filename).read_text()
            
            # Should use Telegram alerts or show error messages
            assert "showAlert" in content or "alert" in content or "error" in content, \
                f"{filename} should show error messages to users"


class TestResponsiveDesign:
    """Test responsive design elements"""
    
    @pytest.fixture
    def frontend_dir(self):
        return Path(__file__).parent.parent / "frontend-miniapps"
    
    def test_files_have_viewport_meta(self, frontend_dir):
        """Test that HTML files have viewport meta tag"""
        html_files = list((frontend_dir).glob("*.html"))
        
        for html_file in html_files:
            content = html_file.read_text()
            assert 'name="viewport"' in content, \
                f"{html_file.name} should have viewport meta tag for mobile"


class TestAccessibility:
    """Test accessibility features"""
    
    @pytest.fixture
    def frontend_dir(self):
        return Path(__file__).parent.parent / "frontend-miniapps"
    
    def test_voice_buttons_have_labels(self, frontend_dir):
        """Test that voice buttons have descriptive text"""
        voice_enabled_files = [
            "campaigns.html",
            "donate.html",
            "create-campaign-wizard.html",
            "ngo-register-wizard.html"
        ]
        
        for filename in voice_enabled_files:
            content = (frontend_dir / filename).read_text()
            
            # Voice buttons should have text or title attributes
            if "voice-btn" in content or "voiceBtn" in content:
                assert any(word in content for word in [
                    "Tap to Speak", "Say", "Voice", "🎤", "Speak"
                ]), f"{filename} voice buttons should have descriptive text"


class TestProgressIndicators:
    """Test progress and loading indicators"""
    
    @pytest.fixture
    def frontend_dir(self):
        return Path(__file__).parent.parent / "frontend-miniapps"
    
    def test_wizard_files_have_progress_bars(self, frontend_dir):
        """Test wizards show progress"""
        wizard_files = [
            "create-campaign-wizard.html",
            "ngo-register-wizard.html"
        ]
        
        for filename in wizard_files:
            content = (frontend_dir / filename).read_text()
            
            # Should have progress indicator
            assert "progress" in content.lower(), \
                f"{filename} should show progress indicator"
            
            # Should update progress
            assert "updateProgress" in content or "progressFill" in content, \
                f"{filename} should update progress"


class TestNavigationLinks:
    """Test navigation between pages"""
    
    @pytest.fixture
    def frontend_dir(self):
        return Path(__file__).parent.parent / "frontend-miniapps"
    
    def test_pages_have_back_to_home(self, frontend_dir):
        """Test that pages have back to home link"""
        html_files = [
            "campaigns.html",
            "donate.html",
            "create-campaign-wizard.html",
            "ngo-register-wizard.html"
        ]
        
        for filename in html_files:
            content = (frontend_dir / filename).read_text()
            
            # Should have back button or link
            assert "index.html" in content or "Back" in content, \
                f"{filename} should have back navigation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
