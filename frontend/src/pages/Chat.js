import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, Send, Loader2, MapPin } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import apiClient from '../apiClient';

function Chat() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const property = state?.property;

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState('');
  const bottomRef = useRef(null);

  useEffect(() => {
    if (!property) return;
    apiClient.getChatHistory(property.id).then(setMessages).catch(() => {});
  }, [property]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isSending) return;
    const userMessage = input.trim();
    setInput('');
    setError('');
    setIsSending(true);

    setMessages((prev) => [
      ...prev,
      { id: `local-user-${Date.now()}`, role: 'user', content: userMessage },
    ]);

    const assistantId = `local-assistant-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: 'assistant', content: '' },
    ]);

    try {
      await apiClient.sendChatMessage(property.id, userMessage, (chunk) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: m.content + chunk } : m
          )
        );
      });
    } catch {
      setError('Failed to send message. Please try again.');
      setMessages((prev) => prev.filter((m) => m.id !== assistantId));
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <main data-testid="chat-page" className="min-h-screen bg-linen-100 pt-14 flex flex-col">
      <div className="max-w-2xl mx-auto w-full px-6 py-10 flex flex-col flex-1">
        {/* Back */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 font-sans text-sm text-ink-400 hover:text-ink-900 transition-colors mb-8 group"
          aria-label="Go back"
        >
          <ArrowLeft size={14} className="group-hover:-translate-x-0.5 transition-transform" />
          Back
        </button>

        {/* Heading */}
        <div className="mb-6 animate-fade-up" style={{ animationFillMode: 'both' }}>
          <h1 className="font-serif text-4xl text-ink-900 mb-2">Chat</h1>
          {property && (
            <div className="flex items-center gap-2">
              <MapPin size={13} className="text-bronze-400" strokeWidth={1.5} />
              <span className="font-sans text-sm text-ink-400">
                {property.formatted_address}
              </span>
            </div>
          )}
        </div>

        {/* Messages */}
        <div
          className="flex-1 bg-white rounded-lg border border-linen-200 p-5 mb-4 overflow-y-auto space-y-4 min-h-64"
          aria-label="Chat messages"
          role="log"
        >
          {messages.length === 0 && (
            <p className="font-sans text-sm text-ink-300 text-center mt-8">
              Ask anything about this property.
            </p>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-2.5 rounded-lg font-sans text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-bronze-500 text-white'
                    : 'bg-linen-100 text-ink-800'
                }`}
                aria-label={msg.role === 'user' ? 'Your message' : 'Assistant message'}
              >
                {msg.role === 'assistant' && msg.content ? (
                  <ReactMarkdown className="prose prose-sm max-w-none">{msg.content}</ReactMarkdown>
                ) : msg.content || (
                  <Loader2 size={13} className="animate-spin text-ink-400" aria-label="Thinking" />
                )}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {error && (
          <p className="font-sans text-sm text-red-700 mb-3" role="alert">
            {error}
          </p>
        )}

        {/* Input */}
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about this property…"
            rows={1}
            aria-label="Message input"
            className="flex-1 px-3 py-2.5 border border-linen-300 rounded-md bg-white font-sans text-sm text-ink-900 placeholder-ink-300 focus:outline-none focus:border-bronze-400 transition-colors resize-none"
          />
          <button
            onClick={handleSend}
            disabled={isSending || !input.trim()}
            aria-label="Send message"
            className="p-2.5 bg-bronze-500 hover:bg-bronze-600 disabled:bg-linen-300 disabled:cursor-not-allowed text-white rounded-md transition-colors flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-bronze-400 focus:ring-offset-1"
          >
            {isSending ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Send size={16} strokeWidth={2} />
            )}
          </button>
        </div>
      </div>
    </main>
  );
}

export default Chat;
