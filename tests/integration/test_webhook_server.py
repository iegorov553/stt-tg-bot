"""Integration tests for webhook server."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from stt_tg_bot.services.webhook_server import webhook_app


class TestWebhookServer:
    """Integration tests for webhook server."""

    def setup_method(self) -> None:
        """Setup test client."""
        self.client = TestClient(webhook_app.get_app())

    def test_health_check_endpoint(self) -> None:
        """Test health check endpoint."""
        response = self.client.get("/")

        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "message": "STT Telegram Bot is running",
        }

    @patch("stt_tg_bot.services.webhook_server.settings")
    def test_webhook_endpoint_valid_token(self, mock_settings) -> None:
        """Test webhook endpoint with valid secret token."""
        mock_settings.webhook_secret = "test_secret"

        # Mock the dispatcher
        with patch.object(webhook_app.dispatcher, "feed_update", new=AsyncMock()):
            response = self.client.post(
                "/tg/test_secret",
                json={
                    "update_id": 123,
                    "message": {
                        "message_id": 1,
                        "date": 1234567890,
                        "chat": {"id": 123, "type": "private"},
                        "from": {"id": 123, "is_bot": False, "first_name": "Test"},
                        "text": "/start",
                    },
                },
                headers={"X-Telegram-Bot-Api-Secret-Token": "test_secret"},
            )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @patch("stt_tg_bot.services.webhook_server.settings")
    def test_webhook_endpoint_invalid_token(self, mock_settings) -> None:
        """Test webhook endpoint with invalid secret token."""
        mock_settings.webhook_secret = "test_secret"

        response = self.client.post(
            "/tg/test_secret",
            json={"update_id": 123},
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_secret"},
        )

        assert response.status_code == 403
        assert "Invalid secret token" in response.json()["detail"]

    @patch("stt_tg_bot.services.webhook_server.settings")
    def test_webhook_endpoint_no_token(self, mock_settings) -> None:
        """Test webhook endpoint without secret token header."""
        mock_settings.webhook_secret = "test_secret"

        response = self.client.post("/tg/test_secret", json={"update_id": 123})

        assert response.status_code == 403

    @patch("stt_tg_bot.services.webhook_server.settings")
    def test_webhook_endpoint_invalid_json(self, mock_settings) -> None:
        """Test webhook endpoint with invalid JSON."""
        mock_settings.webhook_secret = "test_secret"

        response = self.client.post(
            "/tg/test_secret",
            data="invalid json",
            headers={
                "X-Telegram-Bot-Api-Secret-Token": "test_secret",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 422  # Unprocessable Entity

    def test_webhook_endpoint_wrong_path(self) -> None:
        """Test webhook endpoint with wrong path."""
        response = self.client.post(
            "/tg/wrong_secret",
            json={"update_id": 123},
            headers={"X-Telegram-Bot-Api-Secret-Token": "test_secret"},
        )

        assert response.status_code == 404
