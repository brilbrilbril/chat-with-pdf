import { useState, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const API_BASE = '';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [sessionId] = useState(() => uuidv4());
  const [uploadStatus, setUploadStatus] = useState('');
  const [deleteStatus, setDeleteStatus] = useState('');
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || sending) return;

    const userMsg = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setSending(true);

    try {
      const res = await fetch(`/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message: text }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();

      const assistantMsg = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `⚠ Error: ${err.message}`, sources: [] },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadStatus(`Uploading ${file.name}...`);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`/documents/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      setUploadStatus(`✅ ${file.name} ingested`);
      setTimeout(() => setUploadStatus(''), 3000);
    } catch (err) {
      setUploadStatus(`❌ ${err.message}`);
      setTimeout(() => setUploadStatus(''), 4000);
    }

    // Reset input so same file can be re-selected
    e.target.value = '';
  };

  const clearChat = () => {
    setMessages([]);
  };

  const deleteAllDocs = async () => {
    if (!confirm('Delete all documents and clear chat? This cannot be undone.')) return;

    setDeleteStatus('Deleting all documents...');

    try {
      const res = await fetch(`/documents`, {
        method: 'DELETE',
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Delete failed' }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      setMessages([]);
      setDeleteStatus('✅ All documents deleted');
      setTimeout(() => setDeleteStatus(''), 3000);
    } catch (err) {
      setDeleteStatus(`❌ ${err.message}`);
      setTimeout(() => setDeleteStatus(''), 4000);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <div className="header">
        <h1>💬 Chat with PDF</h1>
        <div className="header-actions">
          <button className="btn btn-clear" onClick={clearChat} disabled={messages.length === 0}>
            Clear
          </button>
          <button className="btn btn-delete" onClick={deleteAllDocs}>
            🗑 Delete All
          </button>
        </div>
      </div>

      {/* Upload Zone */}
      <div className="upload-zone">
        <label className="upload-label">
          📎 Upload Document
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.pptx,.xlsx,.csv,.txt"
            onChange={handleFileUpload}
          />
        </label>
        {uploadStatus && <div className="upload-status">{uploadStatus}</div>}
        {deleteStatus && <div className="delete-status">{deleteStatus}</div>}
      </div>

      {/* Chat Area */}
      <div className="chat-area">
        {messages.length === 0 && (
          <div className="empty-state">
            <p>Ask a question about your documents</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
            </div>
            {msg.sources && msg.sources.length > 0 && (
              <div className="sources">
                <div className="sources-title">📚 Sources</div>
                {msg.sources.map((src, j) => (
                  <div key={j} className="source-item">
                    <span className="source-file">{src.file_name}</span>
                    {src.excerpt && <div className="source-excerpt">"{src.excerpt}"</div>}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {sending && (
          <div className="typing">
            <span></span><span></span><span></span>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Bar */}
      <div className="input-bar">
        <input
          type="text"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={sending}
        />
        <button className="btn-send" onClick={sendMessage} disabled={sending || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
