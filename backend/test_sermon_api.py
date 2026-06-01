import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import re

# Import the FastAPI application and utilities from main
from main import app, parse_sermon_markdown, SermonInput

class TestSermonPrepAssistant(unittest.TestCase):
    
    def setUp(self):
        # Create a FastAPI TestClient for endpoint testing
        self.client = TestClient(app)
        
        # High-fidelity mock markdown output from Gloo completions
        self.mock_raw_markdown = """# TITLE: The Grace of Restoration
# MAIN SCRIPTURE: Luke 15:11-32
# MEMORY VERSE: "For this son of mine was dead and is alive again" — Luke 15:24
# CORE THEME: God's grace aggressively pursues our restoration.

## SECTION: OUTLINE
### I. The Rebellion
* Demand for inheritance
* Path of independence

### II. The Return
* Breaking point at pig pen
* Coming to self

## SECTION: SCRIPTURES
### Ephesians 2:4-5 (Supporting Verse)
But because of his great love for us, God, who is rich in mercy, made us alive.

### Romans 5:8 (Supporting Verse)
But God demonstrates his own love for us.

## SECTION: ILLUSTRATIONS
### The Muddy Masterpiece (Historical Illustration)
*Story*: A curator finds a Rembrandt covered in dirt and carefully restores it.
*Application*: Grace is God's restoration solvent for our lives.

## SECTION: DISCUSSION QUESTIONS
1. What does independence from God look like?
2. How does the father running challenge your view of God?

## SECTION: TEACHING NOTES
Leader notes: emphasize unconditional grace. Avoid legalistic pitfalls.
Icebreaker: Share a time you received an undeserved welcome.
"""

    def test_parse_sermon_markdown(self):
        """1. Verify that the markdown parser correctly extracts and structures sections."""
        parsed = parse_sermon_markdown(self.mock_raw_markdown)
        
        # Verify Headers
        self.assertEqual(parsed["title"], "The Grace of Restoration")
        self.assertEqual(parsed["main_scripture"], "Luke 15:11-32")
        self.assertEqual(parsed["memory_verse"], '"For this son of mine was dead and is alive again" — Luke 15:24')
        self.assertEqual(parsed["theme"], "God's grace aggressively pursues our restoration.")
        
        # Verify Outline
        self.assertIn("### I. The Rebellion", parsed["outline"])
        self.assertIn("### II. The Return", parsed["outline"])
        
        # Verify Scriptures List
        self.assertEqual(len(parsed["scriptures"]), 2)
        self.assertEqual(parsed["scriptures"][0]["ref"], "Ephesians 2:4-5")
        self.assertEqual(parsed["scriptures"][0]["role"], "Supporting Verse")
        self.assertIn("rich in mercy", parsed["scriptures"][0]["text"])
        
        # Verify Illustrations List
        self.assertEqual(len(parsed["illustrations"]), 1)
        self.assertEqual(parsed["illustrations"][0]["title"], "The Muddy Masterpiece")
        self.assertEqual(parsed["illustrations"][0]["badge"], "Historical Illustration")
        self.assertEqual(parsed["illustrations"][0]["story"], "A curator finds a Rembrandt covered in dirt and carefully restores it.")
        self.assertEqual(parsed["illustrations"][0]["application"], "Grace is God's restoration solvent for our lives.")
        
        # Verify Discussion Questions List
        self.assertEqual(len(parsed["discussion_questions"]), 2)
        self.assertEqual(parsed["discussion_questions"][0], "What does independence from God look like?")
        
        # Verify Teaching Notes
        self.assertIn("Leader notes:", parsed["teaching_notes"])
        self.assertIn("Icebreaker:", parsed["teaching_notes"])

    @patch("main.get_gloo_token")
    @patch("main.search_gloo")
    @patch("main.requests.post")
    def test_sermon_prep_api_endpoint_success(self, mock_post, mock_search, mock_token):
        """2. Verify that the /sermonai-api/ark-ai POST endpoint handles correct payloads successfully."""
        # Mock token retrieval
        mock_token.return_value = "mock_gloo_oauth_token"
        
        # Mock RAG database vector search response snippets
        mock_search.return_value = [
            {"properties": {"snippet": "But because of his great love for us..."}}
        ]
        
        # Mock Gloo Chat Completions API response
        mock_gloo_resp = MagicMock()
        mock_gloo_resp.status_code = 200
        mock_gloo_resp.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": self.mock_raw_markdown
                    }
                }
            ]
        }
        mock_post.return_value = mock_gloo_resp
        
        # Send Request Payload
        payload = {
            "topic": "Grace and Restoration",
            "scripture": "Luke 15:11-32",
            "style": "Pastoral",
            "duration": "30 mins",
            "audience": "General Congregation",
            "denomination": "Pentecostal / Charismatic",
            "lang": "en"
        }
        
        response = self.client.post("/sermonai-api/ark-ai", json=payload)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("request_id", data)
        self.assertIn("result", data)
        
        result = data["result"]
        self.assertEqual(result["title"], "The Grace of Restoration")
        self.assertEqual(result["style"], "Pastoral")
        self.assertEqual(result["duration"], "30 mins")
        self.assertEqual(result["audience"], "General Congregation")
        self.assertEqual(result["denomination"], "Pentecostal / Charismatic")
        self.assertEqual(len(result["scriptures"]), 2)

        completion_payload = mock_post.call_args.kwargs["json"]
        system_prompt = completion_payload["messages"][0]["content"]
        user_prompt = completion_payload["messages"][1]["content"]
        self.assertIn("Denomination Category: Pentecostal / Charismatic", system_prompt)
        self.assertIn("Holy Spirit", system_prompt)
        self.assertIn("Denomination: 'Pentecostal / Charismatic'", user_prompt)

    def test_sermon_prep_api_endpoint_validation_error(self):
        """3. Verify that sending invalid payloads triggers validation errors (422)."""
        # Missing 'topic' (required field)
        payload = {
            "scripture": "Luke 15:11-32",
            "duration": "30 mins",
            "audience": "General Congregation"
        }
        
        response = self.client.post("/sermonai-api/ark-ai", json=payload)
        
        # Assertions (should trigger validation error)
        self.assertEqual(response.status_code, 422)
        errors = response.json()["detail"]
        missing_fields = [err["loc"][1] for err in errors]
        self.assertIn("topic", missing_fields)

    @patch("main.get_gloo_token")
    @patch("main.requests.post")
    def test_sermon_copilot_api_endpoint_success(self, mock_post, mock_token):
        """4. Verify that the /sermonai-api/copilot POST endpoint handles messages successfully and extracts updated markdown."""
        mock_token.return_value = "mock_gloo_oauth_token"
        
        mock_gloo_resp = MagicMock()
        mock_gloo_resp.status_code = 200
        mock_gloo_resp.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Sure, I have updated the sermon pack outline. [UPDATED_SERMON_PACK]\n# TITLE: Updated Title\n# MAIN SCRIPTURE: John 3:16\n# MEMORY VERSE: \"For God so loved...\" — John 3:16\n# CORE THEME: The love of God.\n## SECTION: OUTLINE\n### I. Point One\n## SECTION: SCRIPTURES\n## SECTION: ILLUSTRATIONS\n## SECTION: DISCUSSION QUESTIONS\n## SECTION: TEACHING NOTES\n[/UPDATED_SERMON_PACK]"
                    }
                }
            ]
        }
        mock_post.return_value = mock_gloo_resp
        
        payload = {
            "messages": [
                {"role": "user", "content": "Update the outline title and add scripture references"}
            ],
            "active_sermon_markdown": "existing markdown text",
            "denomination": "General Christian",
            "style": "Pastoral",
            "lang": "en"
        }
        
        response = self.client.post("/sermonai-api/copilot", json=payload)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("request_id", data)
        self.assertIn("result", data)
        
        result = data["result"]
        self.assertEqual(result["chat_response"], "Sure, I have updated the sermon pack outline.")
        self.assertEqual(result["updated_sermon"], "# TITLE: Updated Title\n# MAIN SCRIPTURE: John 3:16\n# MEMORY VERSE: \"For God so loved...\" — John 3:16\n# CORE THEME: The love of God.\n## SECTION: OUTLINE\n### I. Point One\n## SECTION: SCRIPTURES\n## SECTION: ILLUSTRATIONS\n## SECTION: DISCUSSION QUESTIONS\n## SECTION: TEACHING NOTES")


if __name__ == "__main__":
    print("⛪ Launching SermonForge AI Prep Studio Test Cases...")
    unittest.main()

