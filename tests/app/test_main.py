# src/tests/app/test_main.py

def test_info(client):
    response = client.get('/')
    result = response.get_json()
    assert result is not None
    assert "message" in result
    assert result["message"] == "It Works"


def valid_message(client):
   request_payload = {"activities": [
        {
            "operation": "insert",
            "table": "table1",
            "col_names": ["a", "b", "c"],
            "col_types": ["INTEGER", "STRING", "STRING"],
            "col_values": [1, "BackupAndRestore", "2018-03-27 11:58:28.988414"]
        }]}
   response = client.post("/message", json=request_payload)
   result = response.get_json()

   assert response.status_code == 200
   assert result is not None
   assert "error" in result
   assert result['error'] == None


def invalid_message(client):
   request_payload = {"activities": [
        {
            "operation": "randomstring",
            "table": "table1",
            "col_names": ["a", "b", "c"],
            "col_types": ["INTEGER", "STRING", "STRING"],
            "col_values": [1, "BackupAndRestore", "2018-03-27 11:58:28.988414"]
        }]}
   response = client.post("/message", json=request_payload)
   result = response.get_json()

   assert response.status_code == 200
   assert result is not None
   assert "error" in result
   assert result['error'] == "Invalid Message: 1"
