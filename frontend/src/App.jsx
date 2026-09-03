import { useEffect, useState, useCallback, useRef } from 'react';

import ReactMarkdown from 'react-markdown';
import html2pdf from 'html2pdf.js';

import {
  Search,
  Settings,
  Copy,
  Download,
  Upload,
  Sparkles,
  FileText,
  Sun,
  Moon,
  Plus,
  MessageSquare,
  ChevronDown,
  Send,
  ExternalLink,
  BookOpen,
  GraduationCap,
  ClipboardList,
  Check,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react';

import './App.css';

const API_URL = 'http://127.0.0.1:8000';

/* ────────────────────────────────────────────────────────────────
   Geometric E
──────────────────────────────────────────────────────────────── */

function GeometricE() {
  return (
    <div className="geometric-e-mark">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M6 4h12v2.4H8.8v4.4h7.6v2.4H8.8v4.4H18V20H6V4z"
          fill="currentColor"
        />
      </svg>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────
   Premium Fluid Orb
──────────────────────────────────────────────────────────────── */

function PremiumFluidOrb() {
  return (
    <div className="orb-container">
      <div className="orb-glow-aura" />

      <div className="orb-core">
        <div className="orb-base-layer" />
        <div className="orb-liquid-layer" />
        <div className="orb-depth-layer" />
        <div className="orb-highlight" />
        <div className="orb-rim-shadow" />
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────
   Data Container
──────────────────────────────────────────────────────────────── */

function DataContainer({
  title,
  description,
  actions,
  children,
}) {
  return (
    <div className="data-container">
      <div className="data-container-header">
        <div>
          <h3>{title}</h3>

          {description && <p>{description}</p>}
        </div>

        {actions && (
          <div className="data-container-header-actions">
            {actions}
          </div>
        )}
      </div>

      <div className="data-container-body">
        {children}
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════════
   MAIN APP
════════════════════════════════════════════════════════════════ */

function App() {
  const [input, setInput] = useState('');

  /* ──────────────────────────────────────────────────────────────
     Conversation ID
  ────────────────────────────────────────────────────────────── */

  const [conversationId, setConversationId] = useState(() => {
    const savedConversationId =
      localStorage.getItem('conversationId');

    return savedConversationId
      ? Number(savedConversationId)
      : null;
  });

  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState({});
  const [isStreaming, setIsStreaming] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] =
    useState(false);

  const initialized = useRef(false);

  /* ──────────────────────────────────────────────────────────────
     Theme
  ────────────────────────────────────────────────────────────── */

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'dark';
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((previousTheme) =>
      previousTheme === 'dark' ? 'light' : 'dark'
    );
  }, []);

  /* ──────────────────────────────────────────────────────────────
     Cmd + K
  ────────────────────────────────────────────────────────────── */

  useEffect(() => {
    function handleGlobalKeyDown(event) {
      if (
        (event.metaKey || event.ctrlKey) &&
        event.key === 'k'
      ) {
        event.preventDefault();
      }
    }

    window.addEventListener(
      'keydown',
      handleGlobalKeyDown
    );

    return () => {
      window.removeEventListener(
        'keydown',
        handleGlobalKeyDown
      );
    };
  }, []);

  /* ──────────────────────────────────────────────────────────────
     LOAD HISTORY
  ────────────────────────────────────────────────────────────── */

  async function loadHistory() {
    try {
      const response = await fetch(`${API_URL}/history`);

      if (!response.ok) {
        return {};
      }

      const data = await response.json();

      const backendHistory = data.history || {};

      setHistory(backendHistory);

      return backendHistory;
    } catch (error) {
      console.error(
        'Error loading history:',
        error
      );

      return {};
    }
  }

  /* ──────────────────────────────────────────────────────────────
     LOAD ONE CONVERSATION
  ────────────────────────────────────────────────────────────── */

  async function loadConversation(id) {
    try {
      const response = await fetch(
        `${API_URL}/conversations/${id}`
      );

      if (!response.ok) {
        console.error(
          `Conversation ${id} could not be loaded.`
        );

        return false;
      }

      const data = await response.json();

      const conversationMessages =
        data.history || [];

      setMessages(
        conversationMessages.map((message) => ({
          role: message.role,
          content: message.content,
          sources: message.sources || [],
        }))
      );

      setConversationId(id);

      localStorage.setItem(
        'conversationId',
        String(id)
      );

      return true;
    } catch (error) {
      console.error(
        'Error loading conversation:',
        error
      );

      return false;
    }
  }

  /* ──────────────────────────────────────────────────────────────
     CREATE NEW CONVERSATION
  ────────────────────────────────────────────────────────────── */

  async function createConversation() {
    try {
      const response = await fetch(
        `${API_URL}/conversations`,
        {
          method: 'POST',
        }
      );

      if (!response.ok) {
        throw new Error(
          'Failed to create conversation'
        );
      }

      const data = await response.json();

      const newConversationId =
        Number(data.conversation_id);

      setConversationId(newConversationId);
      setMessages([]);

      localStorage.setItem(
        'conversationId',
        String(newConversationId)
      );

      await loadHistory();
    } catch (error) {
      console.error(
        'Error creating conversation:',
        error
      );
    }
  }

  /* ──────────────────────────────────────────────────────────────
     SEND MESSAGE
  ────────────────────────────────────────────────────────────── */

  async function handleSend() {
    if (
      !input.trim() ||
      isStreaming ||
      conversationId === null
    ) {
      return;
    }

    const userMessage = input.trim();

    setMessages((previousMessages) => [
      ...previousMessages,
      {
        role: 'user',
        content: userMessage,
      },
    ]);

    setInput('');
    setIsStreaming(true);

    try {
      const response = await fetch(
        `${API_URL}/chat/stream`,
        {
          method: 'POST',

          headers: {
            'Content-Type': 'application/json',
          },

          body: JSON.stringify({
            question: userMessage,
            conversation_id: conversationId,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          'Chat request failed'
        );
      }

      if (!response.body) {
        throw new Error(
          'Streaming response is not available'
        );
      }

      const reader =
        response.body.getReader();

      const decoder = new TextDecoder();

      let assistantMessage = '';
      let sources = [];
      let buffer = '';

      while (true) {
        const { value, done } =
          await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, {
          stream: true,
        });

        const lines = buffer.split('\n');

        buffer = lines.pop();

        for (const line of lines) {
          if (!line.trim()) {
            continue;
          }

          const data = JSON.parse(line);

          if (data.type === 'chunk') {
            assistantMessage += data.content;

            setMessages(
              (previousMessages) => {
                const withoutStreaming =
                  previousMessages.filter(
                    (message) =>
                      message.role !==
                      'assistant-streaming'
                  );

                return [
                  ...withoutStreaming,

                  {
                    role: 'assistant-streaming',
                    content:
                      assistantMessage,
                  },
                ];
              }
            );
          }

          if (data.type === 'sources') {
            sources =
              data.sources || [];
          }
        }
      }

      buffer += decoder.decode();

      if (buffer.trim()) {
        const data = JSON.parse(buffer);

        if (data.type === 'chunk') {
          assistantMessage +=
            data.content;
        }

        if (data.type === 'sources') {
          sources =
            data.sources || [];
        }
      }

      setMessages(
        (previousMessages) => {
          const withoutStreaming =
            previousMessages.filter(
              (message) =>
                message.role !==
                'assistant-streaming'
            );

          return [
            ...withoutStreaming,

            {
              role: 'assistant',
              content: assistantMessage,
              sources,
            },
          ];
        }
      );

      await loadHistory();
    } catch (error) {
      console.error(
        'Error sending message:',
        error
      );

      setMessages(
        (previousMessages) => {
          const withoutStreaming =
            previousMessages.filter(
              (message) =>
                message.role !==
                'assistant-streaming'
            );

          return [
            ...withoutStreaming,

            {
              role: 'assistant',
              content:
                'Something went wrong while contacting the ENSIASD Assistant.',
            },
          ];
        }
      );
    } finally {
      setIsStreaming(false);
    }
  }

  /* ──────────────────────────────────────────────────────────────
     ENTER TO SEND
  ────────────────────────────────────────────────────────────── */

  function handleKeyDown(event) {
    if (
      event.key === 'Enter' &&
      !event.shiftKey
    ) {
      event.preventDefault();

      handleSend();
    }
  }

  /* ──────────────────────────────────────────────────────────────
     COPY
  ────────────────────────────────────────────────────────────── */

  function handleCopy(content, index) {
    navigator.clipboard
      .writeText(content)
      .then(() => {
        setCopiedIndex(index);

        setTimeout(
          () => setCopiedIndex(null),
          2000
        );
      });
  }

  /* ──────────────────────────────────────────────────────────────
     DOWNLOAD
  ────────────────────────────────────────────────────────────── */

 async function handleDownload(content, index) {
  const pdfContainer = document.createElement('div');

  pdfContainer.style.width = '700px';
  pdfContainer.style.padding = '40px';
  pdfContainer.style.background = '#ffffff';
  pdfContainer.style.color = '#111111';
  pdfContainer.style.fontFamily =
    'Arial, Helvetica, sans-serif';
  pdfContainer.style.fontSize = '14px';
  pdfContainer.style.lineHeight = '1.6';

  const title = document.createElement('h1');
  title.textContent = 'ENSIASD Academic Assistant';
  title.style.fontSize = '22px';
  title.style.marginBottom = '8px';

  const subtitle = document.createElement('div');
  subtitle.textContent = `Response ${index + 1}`;
  subtitle.style.fontSize = '12px';
  subtitle.style.color = '#666666';
  subtitle.style.marginBottom = '25px';

  const response = document.createElement('div');

  // Convert the Markdown response into readable HTML.
  response.innerHTML = content
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/^- (.*$)/gim, '<li>$1</li>')
    .replace(/\n/g, '<br>');

  response.querySelectorAll('h1, h2, h3').forEach(
    (heading) => {
      heading.style.marginTop = '18px';
      heading.style.marginBottom = '8px';
    }
  );

  response.querySelectorAll('li').forEach((item) => {
    item.style.marginBottom = '4px';
  });

  pdfContainer.appendChild(title);
  pdfContainer.appendChild(subtitle);
  pdfContainer.appendChild(response);

  document.body.appendChild(pdfContainer);

  const options = {
    margin: 10,
    filename: `ensiasd-response-${index + 1}.pdf`,
    image: {
      type: 'jpeg',
      quality: 0.98,
    },
    html2canvas: {
      scale: 2,
      useCORS: true,
    },
    jsPDF: {
      unit: 'mm',
      format: 'a4',
      orientation: 'portrait',
    },
  };

  try {
    await html2pdf()
      .set(options)
      .from(pdfContainer)
      .save();
  } catch (error) {
    console.error(
      'Error generating PDF:',
      error
    );
  } finally {
    document.body.removeChild(pdfContainer);
  }
}

  /* ══════════════════════════════════════════════════════════════
     INITIALIZATION
     
     IMPORTANT FIX:
     
     An existing conversation is valid even if it is EMPTY.
     We therefore DO NOT check `.length > 0`.
     
     Previously:
     
       conversation.length > 0
     
     caused an empty conversation to be considered invalid,
     which created another conversation unnecessarily.
  ══════════════════════════════════════════════════════════════ */

  useEffect(() => {
    if (initialized.current) {
      return;
    }

    initialized.current = true;

    async function initializeApp() {
      try {
        const backendHistory =
          await loadHistory();

        const savedId =
          conversationId;

        /* --------------------------------------------------------
           CASE 1:
           We already have a saved conversation ID and it exists
           in the backend.

           IMPORTANT:
           We accept EMPTY conversations too.
        -------------------------------------------------------- */

        if (
          savedId !== null &&
          Object.prototype.hasOwnProperty.call(
            backendHistory,
            String(savedId)
          )
        ) {
          const loaded =
            await loadConversation(savedId);

          if (loaded) {
            return;
          }
        }

        /* --------------------------------------------------------
           CASE 2:
           Saved ID doesn't exist anymore.

           This usually happens after restarting the backend
           because the current backend stores conversations
           in memory.

           Try to use the newest backend conversation first.
        -------------------------------------------------------- */

        const existingIds =
          Object.keys(backendHistory)
            .map(Number)
            .filter(Number.isFinite)
            .sort((a, b) => b - a);

        if (existingIds.length > 0) {
          const newestId =
            existingIds[0];

          const loaded =
            await loadConversation(
              newestId
            );

          if (loaded) {
            return;
          }
        }

       
        const createResponse =
          await fetch(
            `${API_URL}/conversations`,
            {
              method: 'POST',
            }
          );

        if (!createResponse.ok) {
          throw new Error(
            'Failed to create initial conversation'
          );
        }

        const createData =
          await createResponse.json();

        const newConversationId =
          Number(
            createData.conversation_id
          );

        setConversationId(
          newConversationId
        );

        setMessages([]);

        localStorage.setItem(
          'conversationId',
          String(newConversationId)
        );

        await loadHistory();
      } catch (error) {
        console.error(
          'Error initializing app:',
          error
        );
      }
    }

    initializeApp();
  }, []);

  

  const conversationEntries =
    Object.entries(history)
      .filter(
        ([, conversation]) =>
          conversation &&
          conversation.length > 0
      )
      .sort(
        ([a], [b]) =>
          Number(b) - Number(a)
      );

  

  const currentConversation =
    conversationId !== null
      ? history[String(conversationId)]
      : null;

  const currentUserMessage =
    currentConversation?.find(
      (message) =>
        message.role === 'user'
    )?.content;

  const currentConversationTitle =
    currentUserMessage
      ? currentUserMessage.length > 35
        ? `${currentUserMessage.slice(
            0,
            35
          )}...`
        : currentUserMessage
      : conversationId !== null
        ? `Conversation ${conversationId}`
        : 'New conversation';

  const hasMessages =
    messages.length > 0;

  
  return (
    <div
      className={`app-shell ${
        sidebarCollapsed
          ? 'sidebar-is-collapsed'
          : ''
      }`}
    >
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      {/* ─────────────────────────────────────────────────────────
          SIDEBAR
      ───────────────────────────────────────────────────────── */}

      <aside
        className={`sidebar ${
          sidebarCollapsed
            ? 'collapsed'
            : ''
        }`}
      >
        <div className="sidebar-glow-overlay" />

        <div className="sidebar-top">

          {/* BRAND */}

          <div className="brand">
            <GeometricE />

            {!sidebarCollapsed && (
              <div className="brand-copy">
                <strong>
                  ENSIASD
                </strong>

                <span>
                  Academic AI
                </span>
              </div>
            )}

            <button
              className="sidebar-toggle-btn"
              onClick={() =>
                setSidebarCollapsed(
                  (previous) =>
                    !previous
                )
              }
              aria-label={
                sidebarCollapsed
                  ? 'Expand sidebar'
                  : 'Collapse sidebar'
              }
              title={
                sidebarCollapsed
                  ? 'Expand sidebar'
                  : 'Collapse sidebar'
              }
            >
              {sidebarCollapsed ? (
                <PanelLeftOpen
                  size={16}
                />
              ) : (
                <PanelLeftClose
                  size={16}
                />
              )}
            </button>
          </div>

          {/* NEW CONVERSATION */}

          <button
            className="new-chat-button"
            onClick={
              createConversation
            }
            title="New conversation"
          >
            <Plus size={15} />

            {!sidebarCollapsed && (
              <span>
                New conversation
              </span>
            )}

            {!sidebarCollapsed && (
              <kbd>⌘ N</kbd>
            )}
          </button>

          {/* ASSISTANT */}

          <div className="sidebar-section">
            {!sidebarCollapsed && (
              <div className="section-label">
                ASSISTANT
              </div>
            )}

            <div
              className="sidebar-item active-item"
              title="Academic Assistant"
            >
              <Sparkles size={14} />

              {!sidebarCollapsed && (
                <span>
                  Academic Assistant
                </span>
              )}

              {!sidebarCollapsed && (
                <span className="active-pulse" />
              )}
            </div>
          </div>

          {/* CONVERSATIONS */}

          <div className="sidebar-section history-section">

            {!sidebarCollapsed && (
              <div className="section-heading">

                <div className="section-label">
                  CONVERSATIONS
                </div>

                <span>
                  {conversationEntries.length}
                </span>

              </div>
            )}

            <div className="conversation-list">

              {conversationEntries.length ===
              0 ? (
                !sidebarCollapsed && (
                  <div className="empty-history">
                    Your conversations will appear here.
                  </div>
                )
              ) : (
                conversationEntries.map(
                  ([id, conversation]) => {

                    const firstUserMessage =
                      conversation?.find(
                        (message) =>
                          message.role ===
                          'user'
                      )?.content ||
                      `Conversation ${id}`;

                    const title =
                      firstUserMessage.length >
                      28
                        ? `${firstUserMessage.slice(
                            0,
                            28
                          )}...`
                        : firstUserMessage;

                    return (
                      <button
                        key={id}
                        className={`conversation-item ${
                          Number(id) ===
                          conversationId
                            ? 'selected-conversation'
                            : ''
                        }`}
                        onClick={() =>
                          loadConversation(
                            Number(id)
                          )
                        }
                        title={
                          firstUserMessage
                        }
                      >
                        <MessageSquare
                          size={13}
                        />

                        {!sidebarCollapsed && (
                          <span>
                            {title}
                          </span>
                        )}
                      </button>
                    );
                  }
                )
              )}

            </div>
          </div>
        </div>

        {}

        <div className="sidebar-footer">
          <div className="profile-card">

            <div className="profile-avatar">
              E
            </div>

            {!sidebarCollapsed && (
              <div className="profile-copy">
                <strong>
                  ENSIASD Academic
                </strong>

                <span>
                  Institutional workspace
                </span>
              </div>
            )}

            {!sidebarCollapsed && (
              <span className="profile-menu">
                •••
              </span>
            )}

          </div>
        </div>
      </aside>

      {}

      <main className="main-content">

        {}

        <header className="topbar">

          <div className="topbar-left">

            {sidebarCollapsed && (
              <button
                className="icon-button uncollapse-btn"
                onClick={() =>
                  setSidebarCollapsed(
                    false
                  )
                }
                aria-label="Expand sidebar"
                title="Expand sidebar"
              >
                <PanelLeftOpen
                  size={16}
                />
              </button>
            )}

            <button className="assistant-selector">
              <span className="status-dot" />

              <span>
                ENSIASD Assistant
              </span>

              <ChevronDown
                size={12}
              />
            </button>

          </div>

          <div className="topbar-right">

            {}

            <span
              className="conversation-status"
              title={
                currentConversationTitle
              }
            >
              {currentConversationTitle}
            </span>

            <button
              className="icon-button search-trigger"
              aria-label="Search"
              title="Search (⌘K)"
            >
              <Search size={16} />

              <span className="kbd-hint">
                ⌘K
              </span>
            </button>

            <button
              className="icon-button theme-toggle"
              onClick={toggleTheme}
              aria-label="Toggle theme"
              title={
                theme === 'dark'
                  ? 'Switch to Light Mode'
                  : 'Switch to Dark Mode'
              }
            >
              {theme === 'dark' ? (
                <Sun size={16} />
              ) : (
                <Moon size={16} />
              )}
            </button>

            <div className="settings-wrap">

              <button
                className="icon-button"
                onClick={() =>
                  setShowSettings(
                    (value) => !value
                  )
                }
                aria-label="Open settings"
                title="Settings"
              >
                <Settings size={16} />
              </button>

              {showSettings && (
                <div className="settings-popover">

                  <div className="settings-title">
                    Workspace
                  </div>

                  <div className="settings-row">

                    <span>
                      Theme
                    </span>

                    <span className="settings-value">
                      {theme === 'dark'
                        ? 'Dark (Charcoal)'
                        : 'Light (Slate)'}
                    </span>

                  </div>

                  <div className="settings-row">

                    <span>
                      Mode
                    </span>

                    <span className="settings-value">
                      Academic
                    </span>

                  </div>

                </div>
              )}

            </div>
          </div>
        </header>

        {/* CHAT AREA */}

        <section
          className={`chat-area ${
            hasMessages
              ? 'has-messages'
              : ''
          }`}
        >

          {!hasMessages ? (

            /* WELCOME */

            <div className="welcome-screen">

              <PremiumFluidOrb />

              <div className="eyebrow">
                ENSIASD ACADEMIC ASSISTANT
              </div>

              <h1>
                Your academic information
                <br />
                <span>
                  in one place.
                </span>
              </h1>

              <p className="hero-description">
                Ask questions about ENSIASD
                programs, courses, academic
                procedures and institutional
                documents.
              </p>

              <div className="suggestion-grid">

                <button
                  className="suggestion-card"
                  onClick={() =>
                    setInput(
                      'What are the academic requirements?'
                    )
                  }
                >
                  <span className="suggestion-icon">
                    <GraduationCap
                      size={16}
                    />
                  </span>

                  <span>
                    <strong>
                      Academic requirements
                    </strong>

                    <small>
                      Validation rules and academic
                      regulations.
                    </small>
                  </span>
                </button>

                <button
                  className="suggestion-card"
                  onClick={() =>
                    setInput(
                      'What courses and programs are available?'
                    )
                  }
                >
                  <span className="suggestion-icon">
                    <BookOpen
                      size={16}
                    />
                  </span>

                  <span>
                    <strong>
                      Courses & programs
                    </strong>

                    <small>
                      Curriculum, modules and program
                      information.
                    </small>
                  </span>
                </button>

                <button
                  className="suggestion-card"
                  onClick={() =>
                    setInput(
                      'What academic procedures should I know?'
                    )
                  }
                >
                  <span className="suggestion-icon">
                    <ClipboardList
                      size={16}
                    />
                  </span>

                  <span>
                    <strong>
                      Academic procedures
                    </strong>

                    <small>
                      Institutional procedures and
                      requirements.
                    </small>
                  </span>
                </button>

              </div>
            </div>

          ) : (

            /* MESSAGES */

            <div className="messages-container">

              {messages.map(
                (message, index) => (

                  <div
                    className={`message-row ${
                      message.role ===
                      'user'
                        ? 'user-row'
                        : 'assistant-row'
                    }`}
                    key={index}
                  >

                    <div className="message-avatar">

                      {message.role ===
                      'user' ? (
                        'Y'
                      ) : (
                        <Sparkles
                          size={16}
                        />
                      )}

                    </div>

                    <div className="message-content">

                      <div className="message-author">
                        {message.role ===
                        'user'
                          ? 'You'
                          : 'ENSIASD Assistant'}
                      </div>

                      <div className="message-bubble">

                        <ReactMarkdown>
                          {message.content}
                        </ReactMarkdown>

                        {message.role ===
                          'assistant' &&
                          message.sources &&
                          message.sources.length >
                            0 && (

                            <div className="sources-container">

                              <div className="sources-title">

                                <FileText
                                  size={14}
                                />

                                Sources

                                <small>
                                  {
                                    message
                                      .sources
                                      .length
                                  }{' '}
                                  document
                                  {message
                                    .sources
                                    .length ===
                                  1
                                    ? ''
                                    : 's'}
                                </small>

                              </div>

                              <div className="sources-list">

                                {message.sources.map(
                                  (
                                    source,
                                    sourceIndex
                                  ) => (

                                    <div
                                      className="source-chip"
                                      key={
                                        sourceIndex
                                      }
                                    >

                                      <ExternalLink
                                        size={
                                          12
                                        }
                                      />

                                      <span>
                                        {
                                          source
                                        }
                                      </span>

                                    </div>
                                  )
                                )}

                              </div>

                            </div>
                          )}

                      </div>

                      {/* MESSAGE ACTIONS */}

                      {(message.role ===
                        'assistant' ||
                        message.role ===
                          'assistant-streaming') && (

                        <div className="message-actions">

                          <button
                            className={`action-btn ${
                              copiedIndex ===
                              index
                                ? 'copied'
                                : ''
                            }`}
                            onClick={() =>
                              handleCopy(
                                message.content,
                                index
                              )
                            }
                            aria-label="Copy response"
                            title="Copy to clipboard"
                          >

                            {copiedIndex ===
                            index ? (
                              <Check
                                size={14}
                              />
                            ) : (
                              <Copy
                                size={14}
                              />
                            )}

                          </button>

                          <button
                            className="action-btn"
                            onClick={() =>
                              handleDownload(
                                message.content,
                                index
                              )
                            }
                            aria-label="Download response"
                            title="Download as PDF"
                          >
                            <Download
                              size={14}
                            />
                          </button>

                        </div>
                      )}

                    </div>
                  </div>
                )
              )}

              {isStreaming && (
                <div className="streaming-indicator">

                  <div className="mini-avatar">
                    <Sparkles
                      size={12}
                    />
                  </div>

                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />

                  <em>
                    Generating response...
                  </em>

                </div>
              )}

            </div>
          )}

        </section>

        {/* COMPOSER */}

        <footer className="composer-area">

          <div className="composer">

            <textarea
              value={input}
              placeholder="Ask about ENSIASD..."
              rows="1"
              onChange={(event) =>
                setInput(
                  event.target.value
                )
              }
              onKeyDown={
                handleKeyDown
              }
              disabled={isStreaming}
            />

            <div className="composer-bottom">

              <div className="composer-tools">

                <button
                  className="composer-tool"
                  type="button"
                >
                  <Upload size={12} />

                  <span>
                    Academic context
                  </span>
                </button>

                <span className="composer-hint">
                  Enter to send · Shift + Enter
                  for a new line
                </span>

              </div>

              <button
                className="send-button"
                type="button"
                onClick={handleSend}
                disabled={
                  !input.trim() ||
                  isStreaming
                }
                aria-label="Send message"
              >
                <Send size={16} />
              </button>

            </div>

          </div>

          <div className="footer-note">
            AI-generated answers are grounded in
            available institutional documents.
          </div>

        </footer>

      </main>
    </div>
  );
}

export default App;