# Cognitive Compliance Agent

A comprehensive AI-powered compliance management system that leverages Google's Agent Development Kit (ADK) to provide intelligent compliance monitoring, analysis, and reporting capabilities.

## Overview

This project implements a cognitive compliance agent that can:
- Analyze Anti-Money Laundering (AML) documents and regulations
- Process and understand compliance requirements
- Provide intelligent responses to compliance queries
- Generate compliance reports and recommendations
- Integrate with various data sources for comprehensive analysis

## Project Structure

```
cognitive-compliance-agent/
├── aml_rules_db/           # AML rules database and vector store
├── documents/              # Compliance documents and PDFs
├── frontend/               # React-based web interface
├── my_agents/              # Agent implementations and tools
│   ├── tools/              # Custom tools for agents
│   └── agent.py            # Main agent implementation
├── mcp_server.py           # Model Context Protocol server
├── proxy_server.py         # Proxy server for API management
├── process_docs.py         # Document processing utilities
└── test_backend_direct.py  # Backend testing utilities
```

## Features

### Core Capabilities
- **Document Analysis**: Process and analyze compliance documents using advanced NLP
- **Intelligent Querying**: Natural language interface for compliance questions
- **RAG Integration**: Retrieval-Augmented Generation for accurate responses
- **Multi-Agent System**: Specialized agents for different compliance domains
- **Web Interface**: Modern React-based frontend for user interaction

### Technical Stack
- **Backend**: Python with FastAPI and Vertex AI
- **Frontend**: React with Vite
- **AI/ML**: Google Vertex AI, LangChain, and custom RAG implementations
- **Database**: Vector database for document storage and retrieval
- **Protocol**: Model Context Protocol (MCP) for agent communication

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Cloud Platform account with Vertex AI enabled

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/haransundar/Google-adk.git
   cd cognitive-compliance-agent
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure environment variables**
   Create a `.env` file with your Google Cloud credentials:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
   PROJECT_ID=your-gcp-project-id
   ```

## Usage

### Starting the Backend
```bash
# Start the MCP server
python mcp_server.py

# Start the proxy server
python proxy_server.py
```

### Starting the Frontend
```bash
cd frontend
npm run dev
```

### Using the Agent
The cognitive compliance agent can be accessed through:
- Web interface at `http://localhost:5173`
- Direct API calls to the backend services
- MCP protocol integration

## API Endpoints

### MCP Server
- `/mcp/` - Model Context Protocol endpoints
- `/health` - Health check endpoint

### Proxy Server
- `/api/` - API proxy endpoints
- `/docs` - API documentation

## Development

### Adding New Tools
1. Create a new tool in `my_agents/tools/`
2. Implement the required interface
3. Register the tool in the agent configuration

### Extending Agents
1. Modify `my_agents/agent.py` for core agent logic
2. Add specialized agents in the `my_agents/` directory
3. Update the MCP server to include new agents

### Frontend Development
The frontend is built with React and Vite. Key files:
- `src/App.jsx` - Main application component
- `src/main.jsx` - Application entry point
- `src/styles.css` - Global styles

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Contact the development team
- Check the documentation in the `/docs` directory

## Acknowledgments

- Google Agent Development Kit (ADK) team
- Vertex AI and Google Cloud Platform
- Open source community contributors 