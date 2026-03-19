import { useState, useRef, useEffect } from 'react';
import { sendNLQuery } from '../api';
import { Send, Bot, User, Sparkles, Loader2 } from 'lucide-react';

const SUGGESTIONS = [
  'Which schools have low inclusion scores?',
  'Show dropout risk students',
  'Schools without wheelchair ramps',
  'Rural vs urban comparison',
  'Recommendations to improve inclusion',
  'Show data for Maharashtra',
];

function DataTable({ data }) {
  if (!data || data.length === 0) return null;
  const keys = Object.keys(data[0]);
  return (
    <div className="mt-3 overflow-x-auto rounded-lg border border-slate-200">
      <table className="data-table" style={{ fontSize: 12 }}>
        <thead>
          <tr>
            {keys.map(k => <th key={k}>{k.replace(/_/g, ' ')}</th>)}
          </tr>
        </thead>
        <tbody>
          {data.slice(0, 10).map((row, i) => (
            <tr key={i}>
              {keys.map(k => (
                <td key={k}>
                  {typeof row[k] === 'object' ? (
                    Array.isArray(row[k]) ? row[k].join(', ') : JSON.stringify(row[k])
                  ) : String(row[k])}
                </td>
              ))}
            </tr>
          ))}
          {data.length > 10 && (
            <tr>
              <td colSpan={keys.length} className="text-center text-slate-400 italic">
                + {data.length - 10} more rows
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default function AIAssistant() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: "Namaste! 🙏 I'm the Inclusive Education AI Assistant. Ask me anything about schools, students, inclusion scores, or dropout risk. Try one of the suggestions below!",
      data: null,
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEnd = useRef(null);

  const scrollToBottom = () => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const sendMessage = async (text) => {
    const q = text || input.trim();
    if (!q) return;
    setInput('');

    setMessages(prev => [...prev, { role: 'user', text: q }]);
    setLoading(true);

    try {
      const res = await sendNLQuery(q);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          text: res.answer,
          data: res.data && res.data.length > 0 ? res.data : null,
        },
      ]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          text: "Sorry, I couldn't process that query. Please ensure the backend server is running on port 8000.",
          data: null,
        },
      ]);
    }
    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h2>AI Assistant</h2>
          <p>Ask questions about inclusive education data</p>
        </div>
        <div className="badge badge-info">
          <Sparkles size={12} /> NLP-Powered
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="chat-container">
          {/* Messages */}
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-bubble ${msg.role}`}>
                <div className="flex items-center gap-2 mb-1.5">
                  {msg.role === 'assistant'
                    ? <Bot size={14} className="text-india-500" />
                    : <User size={14} />
                  }
                  <span className="text-[11px] font-semibold opacity-60">
                    {msg.role === 'assistant' ? 'AI Assistant' : 'You'}
                  </span>
                </div>
                <div className="whitespace-pre-line">{msg.text}</div>
                {msg.data && <DataTable data={msg.data} />}
              </div>
            ))}

            {loading && (
              <div className="chat-bubble assistant flex items-center gap-2.5">
                <Loader2 size={16} className="text-slate-400" style={{ animation: 'spin 1s linear infinite' }} />
                <span className="text-[13px] text-slate-400">Analyzing data…</span>
              </div>
            )}
            <div ref={messagesEnd} />
          </div>

          {/* Suggestions */}
          {messages.length <= 1 && (
            <div className="px-5 pb-3 flex flex-wrap gap-2">
              {SUGGESTIONS.map(s => (
                <button key={s} className="btn btn-secondary btn-sm text-[11.5px]"
                  onClick={() => sendMessage(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="chat-input-bar">
            <input
              className="form-input flex-1"
              placeholder="Ask about inclusion, dropout risk, schools…"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              id="ai-chat-input"
            />
            <button className="btn btn-primary" onClick={() => sendMessage()} disabled={loading || !input.trim()} id="ai-chat-send">
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
