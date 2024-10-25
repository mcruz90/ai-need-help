# Ai Need Help: AI Personal Assistant

![image](https://github.com/user-attachments/assets/ac20882c-25b9-4858-9737-7be87d6731b7)

=======

An AI assistant webapp using Cohere's LLM models through a Next.js frontend and a FastAPI backend. It implements a Router Agent that can route user requests to the appropriate agent based on the content of the user's message. The available agents are:

1. a Calendar Agent that calls on tools to modify the user's calendar using Google Calendar API

![image](https://github.com/user-attachments/assets/67df169e-9a7b-4001-8cc2-5cbd6f54da8c)

2. a Web Search Agent that can handle general information-seeking queries and uses Tavily Web Search APIs to ground its responses.


3. a Tutor Agent that can assist students with their school work and provide responses based on the user's stated learning level.

Additionally, the app also uses Notion API to retrieve pages and databases from the user's Notion workspace and a rich-text editor using Tiptap to aid in creating and editing Notion pages, but this is still in the early stages of development.

The prompt template for the tutor agent is based (with some modification)on the Tutor prompt available on [Microsoft's Prompts for Education repository](https://github.com/microsoft/prompts-for-edu/blob/main/Students/Prompts/Tutor.MD).

This project extends the [Cohere Calendar Agent](https://docs.cohere.com/page/calendar-agent) example and the [Cohere Tools on Langchain](https://docs.cohere.com/docs/tools-on-langchain) example for web search and general purpose interactions with Cohere's Command R+ model.

Please note that as with all AI models, outputs may not be completely accurate or reliable. Cohere's models were chosen for this project for their commitment to [responsible AI development](https://cohere.com/responsibility), but as this area is still undergoing a lot of research, the models may still unintentionally generate content that is not appropriate. 

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

5. Set up Google Calendar API:

    - Go to the [Google Cloud Console](https://console.cloud.google.com/)
    - Create a new project/use existing project
    - Enable the Google Calendar API for your project
    - Create credentials (OAuth 2.0 Client ID) and download the `credentials.json` file
    - Place the `credentials.json` file in the `ai-assistant-backend` directory

6. Run the development server:  

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
- [Tiptap Documentation](https://tiptap.dev/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
