import { useState, useEffect, useRef } from 'react'
import './App.css'

// In production, use /api prefix (nginx proxy). In dev, use localhost:8000
const API_URL = import.meta.env.PROD ? '/api' : (import.meta.env.VITE_API_URL || 'http://localhost:8000')

function App() {
  const [command, setCommand] = useState('')
  const [namespace, setNamespace] = useState('')
  const [namespaces, setNamespaces] = useState([])
  const [messages, setMessages] = useState([])
  const [patches, setPatches] = useState([])
  const [loading, setLoading] = useState(false)
  const [connected, setConnected] = useState(false)
  const messagesEndRef = useRef(null)

  // Check health on mount
  useEffect(() => {
    checkHealth()
    fetchNamespaces()
  }, [])

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/health`)
      const data = await res.json()
      setConnected(data.cluster_connected)
    } catch (e) {
      setConnected(false)
    }
  }

  const fetchNamespaces = async () => {
    try {
      const res = await fetch(`${API_URL}/namespaces`)
      const data = await res.json()
      setNamespaces(data.namespaces || [])
    } catch (e) {
      console.error('Failed to fetch namespaces:', e)
    }
  }

  const sendCommand = async (dryRun = true) => {
    if (!command.trim()) return

    setLoading(true)
    setMessages(prev => [...prev, { type: 'user', text: command }])

    try {
      const res = await fetch(`${API_URL}/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: command,
          namespace: namespace || null,
          dry_run: dryRun
        })
      })

      const data = await res.json()

      setMessages(prev => [...prev, {
        type: 'assistant',
        text: data.message || `${data.status}: ${data.patches_count} patches`,
        status: data.status
      }])

      if (data.patches) {
        setPatches(data.patches)
      }

    } catch (e) {
      setMessages(prev => [...prev, {
        type: 'assistant',
        text: `Error: ${e.message}`,
        status: 'error'
      }])
    }

    setLoading(false)
    setCommand('')
  }

  const applyPatches = async () => {
    if (!command.trim()) return
    await sendCommand(false)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendCommand(true)
    }
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-title">
          <span style={{ fontSize: '1.5rem' }}>🔧</span>
          <h1>AI Kustomize Agent</h1>
        </div>
        <div className="header-status">
          <div className={`status-dot ${connected ? '' : 'disconnected'}`}></div>
          <span>{connected ? 'Cluster Connected' : 'Disconnected'}</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Left Panel - Chat */}
        <div className="card">
          <div className="card-header">
            <h2>💬 Command Console</h2>
            <div className="namespace-selector">
              <label>Namespace:</label>
              <select
                value={namespace}
                onChange={(e) => setNamespace(e.target.value)}
              >
                <option value="">All Namespaces</option>
                {namespaces.map(ns => (
                  <option key={ns} value={ns}>{ns}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="card-body">
            <div className="message-list">
              {messages.length === 0 && (
                <div className="empty-state">
                  <div className="empty-state-icon">🚀</div>
                  <p>Enter a command to get started</p>
                  <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
                    Try: "Add label env=prod to all deployments"
                  </p>
                </div>
              )}
              {messages.map((msg, i) => (
                <div key={i} className={`message ${msg.type}`}>
                  {msg.text}
                </div>
              ))}
              {loading && (
                <div className="loading">
                  <div className="loading-spinner"></div>
                  <span>Processing with AI...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          <div className="command-section">
            <div className="command-input-wrapper">
              <input
                type="text"
                className="command-input"
                placeholder="Describe what you want to change..."
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={loading}
              />
              <button
                className="btn btn-primary"
                onClick={() => sendCommand(true)}
                disabled={loading || !command.trim()}
              >
                Preview
              </button>
            </div>
          </div>
        </div>

        {/* Right Panel - Patches */}
        <div className="card">
          <div className="card-header">
            <h2>📋 Patch Preview</h2>
            {patches.length > 0 && (
              <button
                className="btn btn-success"
                onClick={applyPatches}
                disabled={loading}
              >
                🚀 Apply All
              </button>
            )}
          </div>

          <div className="card-body">
            {patches.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">📄</div>
                <p>No patches generated yet</p>
              </div>
            ) : (
              patches.map((patch, i) => (
                <div key={i} className="patch-item">
                  <div className="patch-header">
                    <span className="patch-title">
                      {patch.kind}/{patch.name}
                    </span>
                    <span className="patch-tag">{patch.namespace}</span>
                  </div>
                  <pre className="patch-yaml">{patch.yaml}</pre>
                </div>
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
