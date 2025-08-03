import React, { useState, useRef, useEffect } from "react";

/**
 * Cognitive Compliance Agent (CCA) - Single-file, zero-config, production-ready React App.
 * - All logic, state, markup, and styling is self-contained.
 * - No external CSS, Tailwind, or config required.
 * - Robust backend connection, live streaming, and error handling.
 * - Professional, clean, dark-themed, responsive UI.
 */

//////////////////////
// COLOR PALETTE
//////////////////////
const COLORS = {
  background: "#10141a",      // Page background (very dark blue/gray)
  card: "#1a2233",            // Card background (slightly lighter)
  accent: "#00ffd0",          // Vibrant cyan accent
  border: "#23272f",          // Card border
  error: "#ff3860",           // Error red
  text: "#e5e7eb",            // Main text
  muted: "#94a3b8",           // Muted text
  shadow: "rgba(0,0,0,0.42)", // Card shadow
};

//////////////////////
// STYLE OBJECTS
//////////////////////
const STYLES = {
  root: {
    minHeight: "100vh",
    background: COLORS.background,
    color: COLORS.text,
    fontFamily: "'Inter', ui-sans-serif, system-ui, sans-serif",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    boxSizing: "border-box",
  },
  card: {
    width: "100%",
    maxWidth: 480,
    background: COLORS.card,
    borderRadius: 18,
    boxShadow: `0 4px 32px 0 ${COLORS.shadow}`,
    border: `1.5px solid ${COLORS.border}`,
    padding: 36,
    boxSizing: "border-box",
    marginBottom: 18,
    transition: "box-shadow 0.2s",
  },
  heading: {
    fontSize: 28,
    fontWeight: 800,
    color: COLORS.accent,
    letterSpacing: 1,
    margin: 0,
    textAlign: "center",
  },
  subheading: {
    color: COLORS.muted,
    textAlign: "center",
    fontSize: 15,
    margin: "8px 0 28px 0",
    fontWeight: 400,
  },
  banner: {
    padding: "10px 0",
    borderRadius: 14,
    marginBottom: 18,
    textAlign: "center",
    fontWeight: 600,
    fontSize: 15,
    boxShadow: `0 2px 12px 0 ${COLORS.shadow}`,
    transition: "background 0.2s",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: 16,
  },
  input: {
    background: COLORS.background,
    border: `1.5px solid ${COLORS.border}`,
    borderRadius: 14,
    padding: "14px 16px",
    color: COLORS.text,
    fontSize: 16,
    outline: "none",
    fontFamily: "inherit",
    fontWeight: 500,
    transition: "border 0.2s, box-shadow 0.2s",
    boxShadow: "none",
  },
  inputFocus: {
    border: `1.5px solid ${COLORS.accent}`,
    boxShadow: `0 0 0 2px ${COLORS.accent}55`,
  },
  button: {
    background: COLORS.accent,
    color: COLORS.background,
    fontWeight: 700,
    fontSize: 16,
    border: "none",
    borderRadius: 14,
    padding: "13px 0",
    cursor: "pointer",
    boxShadow: `0 2px 12px 0 ${COLORS.accent}22`,
    transition: "background 0.18s, box-shadow 0.18s",
    outline: "none",
  },
  buttonDisabled: {
    background: "#31ffe1",
    opacity: 0.7,
    cursor: "not-allowed",
  },
  streamBox: {
    marginTop: 24,
    minHeight: 140,
    maxHeight: 260,
    background: COLORS.background,
    border: `1.5px solid ${COLORS.border}`,
    borderRadius: 14,
    padding: 16,
    fontFamily: "'JetBrains Mono', ui-monospace, SFMono-Regular, monospace",
    fontSize: 15,
    color: COLORS.text,
    overflowY: "auto",
    whiteSpace: "pre-wrap",
    transition: "border 0.2s",
  },
  streamPlaceholder: {
    color: COLORS.muted,
    fontStyle: "italic",
  },
  footer: {
    color: COLORS.muted,
    fontSize: 13,
    marginTop: 36,
    textAlign: "center",
    fontWeight: 400,
    letterSpacing: 0.1,
  },
};

//////////////////////
// MAIN APP COMPONENT
//////////////////////
export default function App() {
  // State management for query, streaming response, status, error, and input focus
  const [query, setQuery] = useState("");           // User's query input
  const [response, setResponse] = useState("");     // Streaming agent output
  const [status, setStatus] = useState("idle");     // idle | loading | error | done
  const [error, setError] = useState(null);         // Error message (if any)
  const [inputFocused, setInputFocused] = useState(false); // For input styling
  const scrollRef = useRef(null);                   // For auto-scroll

  // Auto-scroll to bottom on new response chunk
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [response]);

  // Clean up on unmount (no persistent connection in this implementation)
  useEffect(() => {
    return () => {};
  }, []);

  /**
   * Handles form submission:
   * - Sends POST to /run_sse with correct JSON body.
   * - Streams response as text, appending as it arrives ("live typing" effect).
   * - Handles errors gracefully.
   */
  async function handleSubmit(e) {
    e.preventDefault();
    setResponse("");
    setStatus("loading");
    setError(null);

    let controller = new AbortController();

    try {
      const response = await fetch("http://localhost:8000/api/v1/investigate", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`Backend error: ${response.status}`);
      }

      // Stream the response body as text (live typing effect)
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let done = false;

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          setResponse((prev) => prev + chunk);
        }
        done = readerDone;
      }

      setStatus("done");
    } catch (err) {
      // Robust error handling for network/backend issues
      setStatus("error");
      setError(
        "Failed to connect to the compliance agent. Please ensure the backend is running and try again."
      );
    }
    // Cleanup is handled by abort controller and useEffect
  }

  // Banner for errors or loading status
  function StatusBanner() {
    if (status === "error") {
      return (
        <div
          style={{
            ...STYLES.banner,
            background: COLORS.error,
            color: COLORS.text,
            animation: "pulse 1.2s infinite alternate",
          }}
        >
          {error}
        </div>
      );
    }
    if (status === "loading") {
      return (
        <div
          style={{
            ...STYLES.banner,
            background: COLORS.card,
            color: COLORS.accent,
          }}
        >
          <span style={{ animation: "pulse 1.2s infinite alternate" }}>
            Thinking...
          </span>
        </div>
      );
    }
    return null;
  }

  // Main render
  return (
    <div style={STYLES.root}>
      {/* Card Container */}
      <div style={STYLES.card}>
        {/* Heading */}
        <h1 style={STYLES.heading}>Cognitive Compliance Agent</h1>
        <div style={STYLES.subheading}>Enterprise Compliance Dashboard</div>

        {/* Status Banner */}
        <StatusBanner />

        {/* Query Control Panel */}
        <form style={STYLES.form} onSubmit={handleSubmit} autoComplete="off">
          <input
            style={{
              ...STYLES.input,
              ...(inputFocused ? STYLES.inputFocus : {}),
            }}
            type="text"
            placeholder="Enter investigation query..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            required
            spellCheck={false}
            autoFocus
            onFocus={() => setInputFocused(true)}
            onBlur={() => setInputFocused(false)}
            disabled={status === "loading"}
          />
          <button
            style={{
              ...STYLES.button,
              ...(status === "loading" ? STYLES.buttonDisabled : {}),
            }}
            type="submit"
            disabled={status === "loading"}
          >
            {status === "loading" ? "Submitting..." : "Submit"}
          </button>
        </form>

        {/* Streaming Display */}
        <div
          ref={scrollRef}
          style={STYLES.streamBox}
        >
          {response ? (
            <span>{response}</span>
          ) : (
            <span style={STYLES.streamPlaceholder}>
              {status === "idle"
                ? "Awaiting query..."
                : status === "loading"
                ? "Streaming report..."
                : ""}
            </span>
          )}
        </div>
      </div>
      {/* Footer */}
      <footer style={STYLES.footer}>
        Cognitive Compliance Agent © {new Date().getFullYear()} &mdash; Internal Use Only
      </footer>
      {/* Keyframes for pulse animation */}
      <style>
        {`
          @keyframes pulse {
            0% { opacity: 1; }
            100% { opacity: 0.55; }
          }
        `}
      </style>
    </div>
  );
}