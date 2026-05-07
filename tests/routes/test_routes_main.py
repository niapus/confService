from tests.factories import make_conference


class TestShowMain:

    def test_returns_200(self, client, mock_services):
        mock_services["conference"].get_future_conferences.return_value = [make_conference()]
        mock_services["conference"].get_past_conferences.return_value = []
        resp = client.get("/")
        assert resp.status_code == 200

    def test_calls_get_future_conferences(self, client, mock_services):
        mock_services["conference"].get_future_conferences.return_value = []
        mock_services["conference"].get_past_conferences.return_value = []
        client.get("/")
        mock_services["conference"].get_future_conferences.assert_called_once()

    def test_calls_get_past_conferences(self, client, mock_services):
        mock_services["conference"].get_future_conferences.return_value = []
        mock_services["conference"].get_past_conferences.return_value = []
        client.get("/")
        mock_services["conference"].get_past_conferences.assert_called_once()

    def test_empty_conferences(self, client, mock_services):
        mock_services["conference"].get_future_conferences.return_value = []
        mock_services["conference"].get_past_conferences.return_value = []
        resp = client.get("/")
        assert resp.status_code == 200

    def test_with_future_and_past_conferences(self, client, mock_services):
        mock_services["conference"].get_future_conferences.return_value = [
            make_conference(conf_id=1, title="Future Conf"),
            make_conference(conf_id=2, title="Another Future"),
        ]
        mock_services["conference"].get_past_conferences.return_value = [
            make_conference(conf_id=3, title="Past Conf"),
        ]
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.data.decode()
        assert "Future Conf" in data
        assert "Past Conf" in data
