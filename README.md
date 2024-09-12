# Ai Need Help: AI Personal Assistant

An AI assistant webapp using Cohere's LLM models through a Next.js frontend and a FastAPI backend. It currently implements two agents: a Calendar Agent that calls on tools to Google's Calendar API and a Web Search Agent that uses Tavily Web Search APIs. The assistant is currently able to route user requests to the appropriate agent based on the content of the user's message.

Additionally, it also integrates with Notion for enhanced productivity features, but this is still in the early stages of development.

This project extends the [Cohere Calendar Agent](https://docs.cohere.com/page/calendar-agent) example and the [Cohere Tools on Langchain](https://docs.cohere.com/docs/tools-on-langchain) example for web search and general purpose interactions with Cohere's Command R+ model.

## Getting Started

### Prerequisites

- Node.js (version 14 or later)
- Python (version 3.7 or later)
- Google Cloud Platform account
- Cohere API key
- Tavily API key
- Notion API key

### Setup

1. Clone the repository

    ```bash
    git clone https://github.com/mcruz90/ai-need-help.git
    ```

2. Set up the frontend

    ```bash
    cd frontend
    npm install
    ```

3. Set up the backend

    ```bash
    cd backend
    pip install -r requirements.txt
    ```

4. Configure environment variables:

    For the backend:

    ```bash
    cd ai-assistant-backend
    cp .env.example .env
    ```

    Edit the backend `.env` file and add the following information:
    - `COHERE_API_KEY`: Your Cohere API key
    - `TAVILY_API_KEY`: Your Tavily API key
    - `CORS_ORIGINS`: Comma-separated list of allowed origins for CORS (e.g., `http://localhost:3000`)

    For the frontend:

    ```bash
    cd ai-assistant
    cp .env.local.example .env.local
    ```

    Edit the frontend `.env.local` file and add the following information:
    - `NEXT_PUBLIC_BACKEND_URL`: URL of your backend server (e.g., `http://localhost:8000`)
    - `NOTION_TOKEN`: Your Notion API key

5. Run the development server:  

    Frontend:

    ```bash
    cd ai-assistant
    npm run dev
    ```

    Backend:

    ```bash
    cd ai-assistant-backend
    uvicorn main:app --reload
    ```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Features

- AI-powered chat assistant
- Google Calendar integration
- Voice input feature
- Copy functionality for AI responses
- Web search integration using Tavily API
- Notion integration for enhanced productivity

## Development

For a list of planned features and improvements, see [TODO.md](./TODO.md).

## Learn More

To learn more about the resources used in this project, check them out here:

- [Next.js Documentation](https://nextjs.org/docs)
- [Google Calendar API Documentation](https://developers.google.com/calendar)
- [Cohere API Documentation](https://docs.cohere.com/)
- [Cohere Calendar Agent Documentation](https://docs.cohere.com/page/calendar-agent)
- [Tavily API Documentation](https://docs.tavily.com/)
- [Cohere Tools on Langchain](https://docs.cohere.com/docs/tools-on-langchain)
- [Notion API Documentation](https://developers.notion.com/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
