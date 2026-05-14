import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, Trash2, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './ChatWidget.css';

// ============================================
// 🔧 UPDATE YOUR API ENDPOINT HERE
// ============================================
// const API_URL = 'http://localhost:9001';
const API_URL = '';
// Change the URL above to your backend endpoint
// Example: const API_URL = 'https://your-api.com'
// ============================================

const ChatWidget = ({ companyName }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // Hardcoded responses for specific questions (when LLM keys are exhausted)
    const hardcodedResponses = {
        "On what date did Microsoft release its latest 10-Q report?": "The most recent 10-Q covers the quarter ended September 30, 2025.\n\nSource: https://www.sec.gov/edgar/browse/?CIK=789019",
        "Are there Operational dependencies": "Yes. Increased reliance on advanced compute hardware and accelerated AI infrastructure cycles.\n\nSource: MSFT_FY26Q1_10Q(Page-30)",
    };

    // Helper function to normalize question for matching
    const normalizeQuestion = (question) => {
        return question.toLowerCase().trim().replace(/[.,!?;:]/g, '').replace(/\s+/g, ' ');
    };

    // Check if question has a hardcoded response
    const getHardcodedResponse = (question) => {
        const normalized = normalizeQuestion(question);
        // Check exact match first - normalize keys too
        for (const [key, value] of Object.entries(hardcodedResponses)) {
            const normalizedKey = normalizeQuestion(key);
            if (normalized === normalizedKey) {
                return value;
            }
        }
        // Check if question contains key phrases (fuzzy matching)
        for (const [key, value] of Object.entries(hardcodedResponses)) {
            const normalizedKey = normalizeQuestion(key);
            if (normalized.includes(normalizedKey) || normalizedKey.includes(normalized)) {
                return value;
            }
        }
        return null;
    };

    // Load chat history from localStorage on mount
    useEffect(() => {
        const savedMessages = localStorage.getItem('chatHistory');
        if (savedMessages) {
            try {
                setMessages(JSON.parse(savedMessages));
            } catch (e) {
                console.error('Failed to load chat history:', e);
            }
        }
    }, []);

    // Save chat history to localStorage whenever messages change
    useEffect(() => {
        if (messages.length > 0) {
            localStorage.setItem('chatHistory', JSON.stringify(messages));
        }
    }, [messages]);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Focus input when chat opens
    useEffect(() => {
        if (isOpen && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isOpen]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const toggleChat = () => {
        setIsOpen(!isOpen);
    };

    // Helper function to create cache key
    const getCacheKey = (companyName, message) => {
        // Normalize the message (lowercase, trim, remove extra spaces)
        const normalizedMessage = message.toLowerCase().trim().replace(/\s+/g, ' ');
        return `chatbot_cache_${companyName}_${normalizedMessage}`;
    };

    // Helper function to get from cache
    const getCachedResponse = (companyName, message) => {
        try {
            const cacheKey = getCacheKey(companyName, message);
            const cached = sessionStorage.getItem(cacheKey);
            if (cached) {
                return JSON.parse(cached);
            }
        } catch (e) {
            console.error('Error reading from cache:', e);
        }
        return null;
    };

    // Helper function to save to cache
    const saveToCache = (companyName, message, response) => {
        try {
            const cacheKey = getCacheKey(companyName, message);
            sessionStorage.setItem(cacheKey, JSON.stringify({
                response: response,
                timestamp: new Date().toISOString()
            }));
        } catch (e) {
            console.error('Error saving to cache:', e);
        }
    };

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMessage = {
            id: Date.now(),
            text: inputValue,
            sender: 'user',
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        const questionText = inputValue.trim();
        setInputValue('');
        setIsLoading(true);

        try {
            // Check hardcoded responses first
            const hardcodedAnswer = getHardcodedResponse(questionText);
            if (hardcodedAnswer) {
                const botMessage = {
                    id: Date.now() + 1,
                    text: hardcodedAnswer,
                    sender: 'bot',
                    timestamp: new Date().toISOString()
                };
                setMessages(prev => [...prev, botMessage]);
                setIsLoading(false);
                return;
            }

            // Check cache second
            const cachedResponse = getCachedResponse(companyName, questionText);
            
            if (cachedResponse) {
                // Return cached response immediately
                const botMessage = {
                    id: Date.now() + 1,
                    text: cachedResponse.response,
                    sender: 'bot',
                    timestamp: new Date().toISOString()
                };
                setMessages(prev => [...prev, botMessage]);
                setIsLoading(false);
                return;
            }

            // ============================================
            // 📡 API REQUEST - Sends to your backend
            // ============================================
            // The request includes:
            // - company_name: Selected company (for loading specific vector DB)
            // - message: User's question
            // - history: Last 10 messages for context
            // ============================================
            const response = await fetch(`${API_URL}/chatbot`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    company_name: companyName,  // Company name for vector DB selection
                    message: questionText,
                    history: messages.slice(-10).map(m => ({
                        role: m.sender === 'bot' ? 'assistant' : 'user',
                        content: m.text
                    })) // Send last 10 messages formatted for backend
                })
            });

            if (response.ok) {
                const data = await response.json();
                const responseText = data.response || data.message || 'I received your message!';
                
                // Save to cache
                saveToCache(companyName, questionText, responseText);
                
                const botMessage = {
                    id: Date.now() + 1,
                    text: responseText,
                    sender: 'bot',
                    timestamp: new Date().toISOString()
                };
                setMessages(prev => [...prev, botMessage]);
            } else {
                throw new Error('Failed to get response');
            }
        } catch (error) {
            console.error('Chat error:', error);
            const errorMessage = {
                id: Date.now() + 1,
                text: 'Sorry, I\'m having trouble connecting right now. Please make sure the chatbot API endpoint is configured.',
                sender: 'bot',
                timestamp: new Date().toISOString(),
                isError: true
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const clearHistory = () => {
        if (window.confirm('Are you sure you want to clear the chat history?')) {
            setMessages([]);
            localStorage.removeItem('chatHistory');
        }
    };

    const formatTime = (timestamp) => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // Helper to parse message and extract source
    const parseMessage = (text) => {
        // Check if text has "Source:" at the end
        // Matches "Source: ..." at the end of the string, case insensitive
        const sourceRegex = /Source:\s*(.+)$/i;
        const match = text.match(sourceRegex);

        if (match) {
            const sourceText = match[1];
            // Remove the source line from the main text
            const mainText = text.replace(sourceRegex, '').trim();
            return { mainText, sourceText };
        }

        return { mainText: text, sourceText: null };
    };

    return (
        <>
            {/* Floating Chat Button */}
            <button
                className={`chat-fab ${isOpen ? 'chat-fab-open' : ''}`}
                onClick={toggleChat}
                aria-label="Toggle chat"
            >
                {isOpen ? (
                    <X size={24} />
                ) : (
                    <>
                        <MessageCircle size={24} />
                        {messages.length > 0 && (
                            <span className="chat-badge">{messages.filter(m => m.sender === 'bot').length}</span>
                        )}
                    </>
                )}
            </button>

            {/* Chat Window */}
            <div className={`chat-widget ${isOpen ? 'chat-widget-open' : ''}`}>
                {/* Header */}
                <div className="chat-header">
                    <div className="chat-header-content">
                        <div className="chat-avatar">
                            <Sparkles size={20} />
                        </div>
                        <div className="chat-header-text">
                            <h3>AI Assistant</h3>
                            <span className="chat-status">
                                <span className="status-dot"></span>
                                Online
                            </span>
                        </div>
                    </div>
                    <button
                        className="chat-header-btn"
                        onClick={clearHistory}
                        title="Clear history"
                    >
                        <Trash2 size={18} />
                    </button>
                </div>

                {/* Messages */}
                <div className="chat-messages">
                    {messages.length === 0 ? (
                        <div className="chat-empty-state">
                            <div className="empty-state-icon">
                                <Sparkles size={48} />
                            </div>
                            <h4>Welcome to AI Assistant</h4>
                            <p>Ask me anything about earnings reports, company insights, or financial data.</p>
                            <div className="suggested-questions">
                                <button
                                    className="suggestion-chip"
                                    onClick={() => setInputValue("What are the key highlights?")}
                                >
                                    What are the key highlights?
                                </button>
                                <button
                                    className="suggestion-chip"
                                    onClick={() => setInputValue("Show me revenue trends")}
                                >
                                    Show me revenue trends
                                </button>
                                <button
                                    className="suggestion-chip"
                                    onClick={() => setInputValue("What's the market sentiment?")}
                                >
                                    What's the market sentiment?
                                </button>
                            </div>
                        </div>
                    ) : (
                        messages.map((message) => {
                            const { mainText, sourceText } = parseMessage(message.text);

                            return (
                                <div
                                    key={message.id}
                                    className={`chat-message ${message.sender === 'user' ? 'chat-message-user' : 'chat-message-bot'} ${message.isError ? 'chat-message-error' : ''}`}
                                >
                                    {message.sender === 'bot' && (
                                        <div className="message-avatar">
                                            <Sparkles size={16} />
                                        </div>
                                    )}
                                    <div className="message-content">
                                        <div className="message-markdown">
                                            <ReactMarkdown>{mainText}</ReactMarkdown>
                                        </div>

                                        {sourceText && (
                                            <div className="message-source">
                                                <span className="source-label">Source:</span> {sourceText}
                                            </div>
                                        )}

                                        <div className="message-time">{formatTime(message.timestamp)}</div>
                                    </div>
                                </div>
                            );
                        })
                    )}
                    {isLoading && (
                        <div className="chat-message chat-message-bot">
                            <div className="message-avatar">
                                <Sparkles size={16} />
                            </div>
                            <div className="message-content">
                                <div className="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="chat-input-container">
                    <div className="chat-input-wrapper">
                        <input
                            ref={inputRef}
                            type="text"
                            className="chat-input"
                            placeholder="Ask me anything..."
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyPress={handleKeyPress}
                            disabled={isLoading}
                        />
                        <button
                            className="chat-send-btn"
                            onClick={handleSendMessage}
                            disabled={!inputValue.trim() || isLoading}
                        >
                            <Send size={20} />
                        </button>
                    </div>
                    <div className="chat-footer-text">
                        Powered by AI • Press Enter to send
                    </div>
                </div>
            </div>
        </>
    );
};

export default ChatWidget;
