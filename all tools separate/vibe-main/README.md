# Vendor Intelligence & Briefing Engine (VIBE)

A powerful, AI-driven platform for comprehensive vendor analysis, combining real-time earnings insights with an intelligent chat assistant for deep-dive queries.


## 🚀 Tech Stack

- **Frontend**: React + Vite
- **Backend**: FastAPI (Python)
- **AI/LLM**: Google Gemini, LangChain
- **Search**: Tavily API
- **Data**: Yahoo Finance, SEC Filings

## ✨ Features

### 📊 Active Features
- **Highlights and Takeaways**
  - Vendor Discussion Topics
  - **Pricing Insights** (AI-powered with Tavily search)
  - **Products and Features** (New launches, deprecations, regulatory risks)
  - AI, Cloud and Productivity
  - Meta Synergies
  - Meta Spend and Metrics
  
- **Real-time Stock Data**
  - Live stock prices and charts
  - Key metrics (Market Cap, P/E, EPS, Dividend Yield)
  - Historical data (5D, 1M, 6M, 1Y, 5Y)

- **AI-Generated Reports**
  - Quarterly Business Review (QBR)
  - Vendor Briefing Documents
  - Earnings Summary

- **💬 AI Chat Assistant**
  - Real-time interactive Q&A about vendor performance
  - Deep-dive into historical data and market sentiment
  - Context-aware responses based on latest earnings calls

- **Export Functionality**
  - Export reports to Word (.doc) format
  - Formatted with proper headings and lists


### 🔍 AI-Powered Insights
- **Pricing Insights**: Real-time pricing changes with sources
- **Product Features**: New launches, deprecations, and regulatory risks
- **AI Chat Assistant**: Ask specific questions and get immediate, data-backed answers
- **Sources Modal**: Click info (i) button to view sources for AI-generated content


## 📋 Prerequisites

- **Node.js** (v16 or higher)
- **Python** (v3.8 or higher)
- **API Keys**:
  - Google Gemini API Key
  - Tavily API Key

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd vibe
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment Variables
Create a `.env` file in the root directory:
```env
# Google Gemini Configuration
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_LLM_MODEL=gemini-2.0-flash-exp

# Tavily Search API
TAVILY_API_KEY=your_tavily_api_key_here
```

#### Run Backend Server
```bash
uvicorn backend_api:app --reload --port 9001
```

The backend API will be available at `http://localhost:9001`

### 3. Frontend Setup

#### Install Node Dependencies (One-time)
```bash
cd frontend
npm install
```

#### Run Frontend Development Server
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 🏗️ Project Structure

```
vibe/
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── Dashboard.jsx   # Main dashboard
│   │   │   ├── Sidebar.jsx     # Navigation sidebar
│   │   │   ├── ChatWidget.jsx  # AI Chat interface
│   │   │   ├── Hero.jsx        # Landing page
│   │   │   └── ...
│   │   ├── App.jsx             # Main app component
│   │   └── main.jsx            # Entry point
│   ├── package.json
│   └── vite.config.js
│
├── agents/                      # AI agents
│   ├── highlights_agent.py     # Highlights coordinator
│   ├── chatbot_agent.py        # AI Chat assistant agent
│   ├── tavily_search_agent.py  # Tavily search agent
│   └── ...

│
├── tools/                       # LangChain tools
│   ├── pricing_insights_tool.py      # Pricing insights
│   ├── products_features_tool.py     # Product features
│   ├── tavily_search_tool.py         # Tavily search
│   └── ...
│
├── prompts/                     # AI prompts
│   ├── price_insight_prompt.txt      # Pricing insights prompt
│   ├── product_features_prompt.txt   # Product features prompt
│   └── ...
│
├── utils/                       # Utilities
│   ├── llm_client.py           # LLM client wrapper
│   └── config.py               # Configuration
│
├── backend_api.py              # FastAPI backend
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── README.md
```

## 🎯 How It Works

### Architecture Flow

```
Frontend (React) → Backend API (FastAPI) → Highlights Agent → Tools → Tavily Search Agent → Tavily API
                                                                    ↓
                                                              Google Gemini LLM
```

### Key Components

1. **Frontend (React)**
   - User interface with modern design
   - Real-time data fetching
   - Interactive charts and modals
   - Source citations with info buttons

2. **Backend (FastAPI)**
   - RESTful API endpoints
   - Handles data aggregation
   - Coordinates AI agents

3. **AI Agents**
   - **Highlights Agent**: Orchestrates different highlight tabs
   - **Tavily Search Agent**: Performs web searches with custom prompts
   - Uses Google Gemini for intelligent analysis

4. **Tools**
   - **Pricing Insights Tool**: Analyzes pricing changes
   - **Product Features Tool**: Tracks product launches and deprecations
   - Each tool returns structured JSON with content and sources

## 🔧 Configuration

### Adding New Companies

Update the company list in `frontend/src/components/Hero.jsx`:

```javascript
const companies = [
  { name: 'Microsoft', symbol: 'MSFT' },
  { name: 'Apple', symbol: 'AAPL' },
  // Add more companies here
];
```

### Customizing AI Prompts

Edit prompt files in the `prompts/` directory:
- `price_insight_prompt.txt` - Pricing insights format
- `product_features_prompt.txt` - Product features format

### Ngrok Configuration (Optional)

For external access, add your ngrok host to `frontend/vite.config.js`:

```javascript
server: {
  allowedHosts: ['your-ngrok-host.ngrok-free.app'],
  // ...
}
```

## 📊 API Endpoints

### Backend API (Port 9001)

- `POST /highlights` - Get highlights for a specific tab
- `POST /stock-data` - Get real-time stock data
- `POST /company-metrics` - Get company metrics
- `POST /earnings` - Get earnings data
- `POST /chatbot` - Interactive AI assistant for company queries
- `POST /qbr` - Generate QBR report
- `POST /briefing` - Generate briefing document
- `POST /summary` - Get earnings summary


## 🐛 Troubleshooting

### Backend Issues

**API Key Errors**
- Verify `.env` file exists in root directory
- Check API keys are valid and not expired
- Ensure no extra spaces in API keys

**Import Errors**
```bash
pip install -r requirements.txt --upgrade
```

### Frontend Issues

**Module Not Found**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Port Already in Use**
- Change port in `vite.config.js`
- Or kill the process using the port

**Ngrok Host Blocked**
- Add your ngrok host to `allowedHosts` in `vite.config.js`
- Restart the dev server

### AI Agent Issues

**Context Length Exceeded**
- Tavily search is configured to avoid this
- Check `tools/tavily_search_tool.py` settings:
  - `max_results=5`
  - `include_raw_content=False`

**No Sources Returned**
- Check browser console for errors
- Verify Tavily API key is valid
- Check network tab for API responses

## 🚀 Deployment

### Frontend (Vercel/Netlify)
```bash
cd frontend
npm run build
# Deploy the 'dist' folder
```

### Backend (Railway/Render)
```bash
# Ensure requirements.txt is up to date
pip freeze > requirements.txt
# Deploy with start command: uvicorn backend_api:app --host 0.0.0.0 --port $PORT
```

## 📝 Future Enhancements

- [ ] Multi-company comparison
- [ ] Historical earnings trends
- [ ] Sentiment analysis
- [ ] Email alerts for earnings dates
- [ ] PDF export functionality
- [ ] More AI-powered insights tabs
- [ ] Real-time collaboration features

## 📄 License

This project is for internal use.

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 📞 Support

For issues or questions, please contact the development team.

