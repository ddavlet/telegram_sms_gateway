# Telegram SMS Gateway

This project sets up a webhook-based SMS gateway using Telegram and an external SMS service API. It allows users to send bulk SMS messages, manage contacts, and handle interactive commands via Telegram bots.

## Customization:

While the project can be extended and modified, its core functionality is optimized for the described use case. Extensive customization for vastly different purposes may require further modifications.


## Features

- **Webhook Integration**: Receive and process incoming messages and callback queries from Telegram.
- **Bulk SMS Handling**: Send bulk SMS messages to multiple recipients using an external SMS service API.
- **Contact Management**: Import contacts from Excel files and manage them in a JSON database.
- **Interactive Commands**: Support for interactive commands via Telegram bot commands and inline buttons.
- **Security**: Middleware to restrict access based on allowed IP addresses (Telegram IP ranges).

## Setup

### Prerequisites

- Python 3.7+
- Ngrok account (for local development/testing)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/telegram-sms-gateway.git
   cd telegram-sms-gateway
   ```

2. Install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file and provide necessary API tokens and credentials.

4. Run the application:
   ```bash
   fastapi run --port PORT main.py
   ```

5. Use Ngrok (for local testing):
   - Install Ngrok: [Ngrok Installation Guide](https://ngrok.com/download)

## Usage
- **Sending Test SMS**: Send test SMS messages by using the `/test <message>` command in Telegram.
- **Sending Bulk SMS**: Send bulk SMS messages by using the `/bulk <message>` command in Telegram.
- **Managing Contacts**: Import contacts from an Excel file and manage them using the Telegram bot commands.
- **Interactive Commands**: Use inline buttons for user interaction and command confirmation.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- FastAPI: Web framework for building APIs with Python.
- Ngrok: Secure tunneling tool for exposing local servers to the internet.
- Telegram API: Documentation and support for Telegram bot integration.

---
