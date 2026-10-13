import { useEffect, useRef, useState } from 'react';

import './App.css';

import UploadCard from './components/UploadCard';

import AskAI from './components/AskAI';

import SearchHistory from './components/SearchHistory';

import { getSpeechRecognitionCtor, resolveVoiceError } from './voiceUtils';



const defaultSearches = [

  { question: 'What is RAG?', date: new Date().toISOString(), results: 3, status: 'Relevant results' },

  { question: 'What is Machine Learning?', date: new Date().toISOString(), results: 2, status: 'Relevant results' },

  { question: 'What is ChromaDB?', date: new Date().toISOString(), results: 2, status: 'Relevant results' },

];



const defaultDocuments = [

  { name: 'sample.pdf', type: 'PDF', status: 'Indexed', chunks: 6, source: 'Uploaded sample' },

  { name: 'education.txt', type: 'TXT', status: 'Indexed', chunks: 4, source: 'Uploaded education file' },

  { name: 'technology.txt', type: 'TXT', status: 'Indexed', chunks: 2, source: 'Uploaded technology file' },

];



const normalizeHistory = (items = []) =>

  items.map((item) => {

    if (typeof item === 'string') {

      return {

        question: item,

        date: new Date().toISOString(),

        results: 0,

        status: 'Recent',

      };

    }



    return {

      question: item.question || 'Untitled question',

      date: item.date || new Date().toISOString(),

      results: item.results ?? 0,

      status: item.status || 'Recent',

    };

  });



const hasSpeechSupport = () => Boolean(getSpeechRecognitionCtor(window));



const sectionMenuItems = [

  { label: 'Knowledge Base', sectionIndex: 2 },

  { label: 'Ask AI', sectionIndex: 1 },

  { label: 'Search History', sectionIndex: 3 },

  { label: 'Settings', sectionIndex: 4 },

  { label: 'Dashboard', sectionIndex: 0 },

];



const stats = [

  { title: 'Documents', icon: '📄', value: '4+' },

  { title: 'Queries', icon: '🔎', value: 'Live' },

  { title: 'Retrieval', icon: '⚡', value: 'Semantic' },

  { title: 'Confidence', icon: '📊', value: 'Tracked' },

];



function App() {

  const [selectedFile, setSelectedFile] = useState(null);

  const [question, setQuestion] = useState('');

  const [results, setResults] = useState([]);

  const [emptyMessage, setEmptyMessage] = useState('');

  const [answerDetails, setAnswerDetails] = useState({

    queryType: '',

    classificationConfidence: null,

    answer: '',

    sources: [],

    confidence: { label: '', score: 0 },

    status: '',

    retrievedChunks: [],

    conversationContext: null,

  });

  const [clarificationState, setClarificationState] = useState({

    pending: false,

    question: '',

    originalQuery: '',

  });

  const [selectedTopK, setSelectedTopK] = useState(3);

  const [voiceState, setVoiceState] = useState({

    transcript: '',

    speaking: false,

    error: '',

  });

  const [uploadState, setUploadState] = useState({

    message: '',

    type: 'info',

    success: false,

    details: null,

  });

  const [isUploading, setIsUploading] = useState(false);

  const [isSearching, setIsSearching] = useState(false);

  const [menuOpen, setMenuOpen] = useState(false);

  const [activeSection, setActiveSection] = useState(0);

  const [searchHistory, setSearchHistory] = useState(() => {

    const saved = localStorage.getItem('ai-knowledge-searches');

    if (!saved) return defaultSearches;



    try {

      const parsed = JSON.parse(saved);

      return normalizeHistory(Array.isArray(parsed) ? parsed : []);

    } catch {

      return defaultSearches;

    }

  });

  const [uploadedDocuments, setUploadedDocuments] = useState(() => {

    const saved = localStorage.getItem('ai-knowledge-documents');

    if (!saved) return defaultDocuments;



    try {

      const parsed = JSON.parse(saved);

      return Array.isArray(parsed) ? parsed : defaultDocuments;

    } catch {

      return defaultDocuments;

    }

  });

  const [theme, setTheme] = useState('light');
  const [analytics, setAnalytics] = useState({
    summary: { total_queries: 0, successful_answers: 0, unanswered_queries: 0, low_confidence_queries: 0, clarification_queries: 0, query_types: {}, domains: {} },
    knowledge_gaps: [],
    total_records: 0,
  });
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [analyticsError, setAnalyticsError] = useState('');


  const [sessionId] = useState(() => {

    const savedSessionId = localStorage.getItem('ai-knowledge-session-id');



    if (savedSessionId) {

      return savedSessionId;

    }



    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

    localStorage.setItem('ai-knowledge-session-id', newSessionId);

    return newSessionId;

  });

  const scrollerRef = useRef(null);

  const sectionRefs = useRef([]);



  useEffect(() => {

    const storedTheme = localStorage.getItem('ai-knowledge-theme') || 'light';

    setTheme(storedTheme);

    document.body.dataset.theme = storedTheme;

  }, []);

  const fetchAnalytics = async () => {
    try {
      setAnalyticsLoading(true);
      setAnalyticsError('');
      const response = await fetch('http://127.0.0.1:5000/analytics/statistics');
      const data = await response.json();
      if (!response.ok || data.status !== 'success') throw new Error(data.message || 'Failed to load analytics.');
      const statistics = data.statistics || {};
      setAnalytics({
        summary: {
          total_queries: statistics.summary?.total_queries ?? 0,
          successful_answers: statistics.summary?.successful_answers ?? 0,
          unanswered_queries: statistics.summary?.unanswered_queries ?? 0,
          low_confidence_queries: statistics.summary?.low_confidence_queries ?? 0,
          clarification_queries: statistics.summary?.clarification_queries ?? 0,
          query_types: statistics.summary?.query_types || {},
          domains: statistics.summary?.domains || {},
        },
        knowledge_gaps: Array.isArray(statistics.knowledge_gaps) ? statistics.knowledge_gaps : [],
        total_records: statistics.total_records ?? 0,
      });
    } catch (error) {
      console.error('Analytics loading error:', error);
      setAnalyticsError('Could not load analytics data.');
    } finally {
      setAnalyticsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 10000);
    return () => clearInterval(interval);
  }, []);



  useEffect(() => {

    localStorage.setItem('ai-knowledge-searches', JSON.stringify(searchHistory));

  }, [searchHistory]);



  useEffect(() => {

    localStorage.setItem('ai-knowledge-documents', JSON.stringify(uploadedDocuments));

  }, [uploadedDocuments]);



  useEffect(() => {

    document.body.dataset.theme = theme;

    localStorage.setItem('ai-knowledge-theme', theme);

  }, [theme]);



  const scrollToSection = (index) => {

    const section = sectionRefs.current[index];

    const container = scrollerRef.current;



    if (!section || !container) return;

    section.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });

    setActiveSection(index);

    setMenuOpen(false);

  };



  const handleScroll = () => {

    const container = scrollerRef.current;

    if (!container) return;



    const index = Math.min(

      sectionRefs.current.length - 1,

      Math.max(0, Math.round(container.scrollLeft / window.innerWidth))

    );

    setActiveSection(index);

  };



  const handleWheel = (event) => {

    const container = scrollerRef.current;

    if (!container) return;



    if (Math.abs(event.deltaY) > 0 && !event.shiftKey && !event.ctrlKey) {

      event.preventDefault();

      container.scrollLeft += event.deltaY;

    }

  };



  const handleSelectQuestion = (questionText) => {

    if (!questionText) return;

    setQuestion(questionText);

    setEmptyMessage('');

    setUploadState({ message: '', type: 'info', success: false, details: null });

  };



  const handleUpload = async (fileArg = selectedFile, action = 'upload') => {

    if (action === 'selected' && fileArg) {

      setUploadState({ message: '', type: 'info', success: false, details: null });

      return;

    }



    if (!fileArg) {

      setUploadState({

        message: 'Please select a document first.',

        type: 'error',

        success: false,

        details: null,

      });

      return;

    }



    const fileExtension = `.${fileArg.name.split('.').pop().toLowerCase()}`;

    if (!['.pdf', '.docx', '.txt', '.csv'].includes(fileExtension)) {

      setUploadState({

        message: 'Unsupported file format.',

        type: 'error',

        success: false,

        details: null,

      });

      return;

    }



    setIsUploading(true);

    setUploadState({

      message: 'Uploading document...',

      type: 'info',

      success: false,

      details: null,

    });



    const formData = new FormData();

    formData.append('file', fileArg);



    try {

      const response = await fetch('http://127.0.0.1:5000/upload', {

        method: 'POST',

        body: formData,

      });



      const data = await response.json();



      if (response.ok) {

        const filename = data.filename || fileArg.name;

        const numberOfChunks = data.number_of_chunks ?? 0;



        setUploadState({

          message: '✓ Document uploaded successfully',

          type: 'success',

          success: true,

          details: { filename, number_of_chunks: numberOfChunks },

        });



        const extension = filename.split('.').pop().toUpperCase();

        setUploadedDocuments((prev) => {

          const isDuplicate = prev.some((doc) => doc.name === filename);

          if (isDuplicate) {

            return prev;

          }

          return [...prev, { name: filename, type: extension, status: 'Indexed', chunks: numberOfChunks, source: 'Uploaded document' }];

        });

      } else {

        setUploadState({

          message: data.error || 'Something went wrong while uploading.',

          type: 'error',

          success: false,

          details: null,

        });

      }

    } catch (error) {

      setUploadState({

        message: 'Could not connect to the backend.',

        type: 'error',

        success: false,

        details: null,

      });

    } finally {

      setIsUploading(false);

    }

  };



  const handleAsk = async (questionOverride = null) => {

    const trimmedQuestion = (questionOverride ?? question).trim();

    const normalizedTopK = [1, 3, 5].includes(selectedTopK) ? selectedTopK : 3;



    if (!trimmedQuestion) {

      setResults([]);

      setEmptyMessage('Please enter a question first.');

      setUploadState({

        message: 'Please enter a question first.',

        type: 'error',

        success: false,

        details: null,

      });

      return;

    }



    setIsSearching(true);

    setUploadState({ message: '', type: 'info', success: false, details: null });

    setEmptyMessage('');



    try {

      const payload = clarificationState.pending

        ? {

            question: trimmedQuestion,

            original_query: clarificationState.originalQuery,

            clarification_response: trimmedQuestion,

            top_k: normalizedTopK,

            session_id: sessionId,

          }

        : {

            question: trimmedQuestion,

            top_k: normalizedTopK,

            session_id: sessionId,

          };



      const response = await fetch('http://127.0.0.1:5000/ask', {

        method: 'POST',

        headers: { 'Content-Type': 'application/json' },

        body: JSON.stringify(payload),

      });



      const data = await response.json();



      if (response.ok) {

        const retrievedChunks = Array.isArray(data.retrieved_chunks) ? data.retrieved_chunks : [];

        const normalizedAnswer = data.answer || (retrievedChunks.length ? 'Answer generated.' : 'No relevant information was found in the current knowledge base.');



        const clarificationQuestion = data.clarification?.clarification_question || '';

        if (data.status === 'clarification_required' && clarificationQuestion) {

          setClarificationState({

            pending: true,

            question: clarificationQuestion,

            originalQuery: data.query || trimmedQuestion,

          });

          fetchAnalytics();

      } else {

          setClarificationState({ pending: false, question: '', originalQuery: '' });

        }
        const responseTopK = [1, 3, 5].includes(Number(data.top_k))

          ? Number(data.top_k)

          : normalizedTopK;

        setSelectedTopK(responseTopK);

        setResults(retrievedChunks);

        setAnswerDetails({

          queryType: data.query_type || 'unknown',

          classificationConfidence: data.classification_confidence ?? null,

          answer: normalizedAnswer,

          sources: Array.isArray(data.sources) ? data.sources : [],

          confidence: data.confidence || { label: 'Low', score: 0 },

          status: data.status || 'success',

          retrievedChunks,

          topK: responseTopK,

          conversationContext: data.conversation_context || null,

        });

        setEmptyMessage(data.answer || data.message || (retrievedChunks.length === 0 ? normalizedAnswer : ''));



        if (data.status !== 'clarification_required') {

          setSearchHistory((prev) => {

            const normalizedPrevious = normalizeHistory(prev);

            const next = [

              {

                question: data.refined_query || trimmedQuestion,

                date: new Date().toISOString(),

                results: retrievedChunks.length,

                status: retrievedChunks.length > 0 ? 'Relevant results' : 'No relevant results',

              },

              ...normalizedPrevious.filter((entry) => entry.question !== (data.refined_query || trimmedQuestion)),

            ];

            return next.slice(0, 10);

          });

        }

      } else {

        setResults([]);

        setAnswerDetails({

          queryType: 'unknown',

          classificationConfidence: null,

          answer: data.error || 'Something went wrong while searching.',

          sources: [],

          confidence: { label: 'Low', score: 0 },

          status: data.status || 'error',

          retrievedChunks: [],

          conversationContext: null,

        });

        setEmptyMessage(data.error || 'Something went wrong while searching.');

        setUploadState({

          message: data.error || 'Something went wrong while searching.',

          type: 'error',

          success: false,

          details: null,

        });

      }

    } catch (error) {

      setResults([]);

      setAnswerDetails({

        queryType: 'unknown',

        classificationConfidence: null,

        answer: 'Could not connect to the backend.',

        sources: [],

        confidence: { label: 'Low', score: 0 },

        status: 'backend_error',

        retrievedChunks: [],

        conversationContext: null,

      });

      setEmptyMessage('Could not connect to the backend.');

      setUploadState({

        message: 'Could not connect to the backend.',

        type: 'error',

        success: false,

        details: null,

      });

    } finally {

      setIsSearching(false);

    }

  };



  const handleVoiceStart = () => {

    const SpeechRecognition = getSpeechRecognitionCtor(window);

    const isSecureContext =

      window.isSecureContext ||

      location.protocol === 'https:' ||

      location.hostname === 'localhost' ||

      location.hostname === '127.0.0.1';



    if (!SpeechRecognition) {

      setVoiceState({

        transcript: '',

        speaking: false,

        error: resolveVoiceError({

          speechRecognitionSupported: false,

          navigatorSecure: isSecureContext,

          permissionGranted: true,

        }),

      });

      return;

    }



    if (!isSecureContext) {

      setVoiceState({

        transcript: '',

        speaking: false,

        error: resolveVoiceError({

          speechRecognitionSupported: true,

          navigatorSecure: false,

          permissionGranted: true,

        }),

      });

      return;

    }



    const sessionId = Date.now();

    window.speechRecognitionSessionId = sessionId;



    const oldRecognition = window.speechRecognitionInstance;

    if (oldRecognition) {

      try {

        oldRecognition.abort();

      } catch (error) {

      }

    }



    const recognition = new SpeechRecognition();

    recognition.lang = 'en-US';

    recognition.continuous = false;

    recognition.interimResults = true;

    recognition.maxAlternatives = 1;

    window.speechRecognitionInstance = recognition;



    recognition.onstart = () => {

      if (window.speechRecognitionSessionId !== sessionId) return;

      setVoiceState({ transcript: '', speaking: true, error: '' });

    };



    recognition.onresult = (event) => {

      if (window.speechRecognitionSessionId !== sessionId) return;



      let transcript = '';

      for (let i = event.resultIndex; i < event.results.length; i += 1) {

        const result = event.results[i];

        if (result && result[0]) transcript += `${result[0].transcript} `;

      }



      transcript = transcript.trim();

      if (!transcript) return;



      setQuestion(transcript);

      setVoiceState({ transcript, speaking: true, error: '' });



      const lastResult = event.results[event.results.length - 1];

      if (lastResult && lastResult.isFinal) {

        setVoiceState({ transcript, speaking: false, error: '' });

        setTimeout(() => {

          if (window.speechRecognitionSessionId !== sessionId) return;

          handleAsk(transcript);

        }, 300);

      }

    };



    recognition.onerror = (event) => {

      if (window.speechRecognitionSessionId !== sessionId) return;



      const errorMessage = event?.error || '';

      if (errorMessage === 'aborted') return;



      if (errorMessage === 'no-speech') {

        setVoiceState({

          transcript: '',

          speaking: false,

          error: 'No speech was recognized. Please try again.',

        });

        return;

      }



      if (errorMessage === 'not-allowed') {

        setVoiceState({

          transcript: '',

          speaking: false,

          error: resolveVoiceError({

            speechRecognitionSupported: true,

            navigatorSecure: true,

            permissionGranted: false,

          }),

        });

        return;

      }



      setVoiceState({

        transcript: '',

        speaking: false,

        error: resolveVoiceError({

          speechRecognitionSupported: true,

          navigatorSecure: true,

          permissionGranted: true,

          browserError: errorMessage,

          fallbackMessage: `Speech recognition error: ${errorMessage}`,

        }),

      });

    };



    recognition.onend = () => {

      if (window.speechRecognitionSessionId !== sessionId) return;

      setVoiceState((prev) => ({ ...prev, speaking: false }));

      if (window.speechRecognitionInstance === recognition) {

        window.speechRecognitionInstance = null;

      }

    };



    try {

      recognition.start();

      setVoiceState({ transcript: '', speaking: true, error: '' });

    } catch (error) {

      setVoiceState({

        transcript: '',

        speaking: false,

        error: resolveVoiceError({

          speechRecognitionSupported: true,

          navigatorSecure: isSecureContext,

          permissionGranted: true,

          fallbackMessage: 'Speech recognition could not start in this browser. Please try again.',

        }),

      });

    }

  };



  const handleVoiceStop = () => {

    window.speechRecognitionSessionId = null;

    const recognition = window.speechRecognitionInstance;

    if (recognition) {

      try {

        recognition.stop();

      } catch (error) {

      }

    }

    window.speechRecognitionInstance = null;

    setVoiceState((prev) => ({ ...prev, speaking: false, error: '' }));

  };



  const handleSpeakAnswer = () => {

    if (!answerDetails?.answer) return;



    const synth = window.speechSynthesis;

    if (!synth) {

      setVoiceState((prev) => ({ ...prev, error: 'Speech synthesis is not supported in this browser.' }));

      return;

    }



    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(answerDetails.answer);

    utterance.lang = 'en-US';

    utterance.onstart = () => setVoiceState((prev) => ({ ...prev, speaking: true, error: '' }));

    utterance.onend = () => setVoiceState((prev) => ({ ...prev, speaking: false, error: '' }));

    utterance.onerror = () => setVoiceState((prev) => ({ ...prev, speaking: false, error: 'Speech synthesis failed.' }));

    synth.speak(utterance);

  };



  const handleSpeechPause = () => {

    if (window.speechSynthesis) {

      window.speechSynthesis.pause();

    }

  };



  const handleSpeechResume = () => {

    if (window.speechSynthesis) {

      window.speechSynthesis.resume();

    }

  };



  const handleSpeechStop = () => {

    if (window.speechSynthesis) {

      window.speechSynthesis.cancel();

      setVoiceState((prev) => ({ ...prev, speaking: false }));

    }

  };



  return (

    <div className="app-shell">

      <div className="floating-menu-wrap">

        <button type="button" className="menu-button" onClick={() => setMenuOpen((open) => !open)}>

          ☰ Menu

        </button>



        {menuOpen && (

          <div className="nav-panel">

            {sectionMenuItems.map((item) => (

              <button

                key={item.label}

                type="button"

                className={`nav-panel-item ${activeSection === item.sectionIndex ? 'active' : ''}`}

                onClick={() => scrollToSection(item.sectionIndex)}

              >

                {item.label}

              </button>

            ))}

          </div>

        )}

      </div>



      <div className="horizontal-scroll" ref={scrollerRef} onScroll={handleScroll} onWheel={handleWheel}>

        <section className="page-section dashboard-section" ref={(el) => { sectionRefs.current[0] = el; }}>

          <div className="section-inner dashboard-inner">

            <div className="dashboard-hero card-panel">

              <div>

                <p className="eyebrow">AI Knowledge Retrieval Platform</p>

                <h1>AI Knowledge Retrieval Platform</h1>

                <p className="hero-subtitle">Intelligent document search and question answering</p>

              </div>

              <span className="status-badge">Live Retrieval</span>

            </div>



            <div className="stats-grid">

              {stats.map((card) => (

                <div className="stat-card card-panel" key={card.title}>

                  <div className="stat-icon">{card.icon}</div>

                  <div>

                    <div className="stat-title">{card.title}</div>

                    <div className="stat-value">{card.value}</div>

                  </div>

                </div>

              ))}

            </div>



            <div className="analytics-section card-panel" style={{ marginTop: '20px', padding: '22px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px', marginBottom: '18px', flexWrap: 'wrap' }}>
                <div>
                  <p className="eyebrow" style={{ marginBottom: '4px' }}>M4.1 Analytics</p>
                  <h2 style={{ margin: 0 }}>Query Analytics &amp; Knowledge Gaps</h2>
                  <p style={{ margin: '6px 0 0', opacity: 0.72 }}>Live usage, query resolution, confidence and knowledge coverage.</p>
                </div>
                <div style={{ fontSize: '13px', opacity: 0.75 }}>{analyticsLoading ? 'Updating...' : `${analytics.total_records} records`}</div>
              </div>
              {analyticsError && <div style={{ padding: '10px 12px', marginBottom: '16px', borderRadius: '10px', background: 'rgba(220, 38, 38, 0.08)' }}>{analyticsError}</div>}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px', marginBottom: '18px' }}>
                {[
                  ['🔎', 'Total Queries', analytics.summary.total_queries],
                  ['✅', 'Successful Answers', analytics.summary.successful_answers],
                  ['⚠️', 'Unanswered', analytics.summary.unanswered_queries],
                  ['📉', 'Low Confidence', analytics.summary.low_confidence_queries],
                  ['💬', 'Clarifications', analytics.summary.clarification_queries],
                ].map(([icon, label, value]) => (
                  <div key={label} style={{ padding: '16px', borderRadius: '12px', border: '1px solid rgba(100, 116, 139, 0.18)' }}>
                    <div style={{ fontSize: '20px', marginBottom: '6px' }}>{icon}</div>
                    <div style={{ fontSize: '12px', opacity: 0.7 }}>{label}</div>
                    <div style={{ fontSize: '24px', fontWeight: 700, marginTop: '3px' }}>{value}</div>
                  </div>
                ))}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
                <div style={{ padding: '16px', borderRadius: '12px', border: '1px solid rgba(100, 116, 139, 0.18)' }}>
                  <h3 style={{ marginTop: 0 }}>Query Types</h3>
                  {Object.entries(analytics.summary.query_types).length === 0 ? <p style={{ opacity: 0.65 }}>No query data yet.</p> : Object.entries(analytics.summary.query_types).map(([type, count]) => (
                    <div key={type} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(100, 116, 139, 0.10)' }}><span style={{ textTransform: 'capitalize' }}>{type}</span><strong>{count}</strong></div>
                  ))}
                </div>
                <div style={{ padding: '16px', borderRadius: '12px', border: '1px solid rgba(100, 116, 139, 0.18)' }}>
                  <h3 style={{ marginTop: 0 }}>Knowledge Domains</h3>
                  {Object.entries(analytics.summary.domains).length === 0 ? <p style={{ opacity: 0.65 }}>No domain data yet.</p> : Object.entries(analytics.summary.domains).map(([domain, count]) => (
                    <div key={domain} style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', padding: '8px 0', borderBottom: '1px solid rgba(100, 116, 139, 0.10)' }}><span style={{ overflowWrap: 'anywhere' }}>{domain}</span><strong>{count}</strong></div>
                  ))}
                </div>
              </div>
              <div style={{ marginTop: '16px', padding: '16px', borderRadius: '12px', border: '1px solid rgba(100, 116, 139, 0.18)' }}>
                <h3 style={{ marginTop: 0 }}>Detected Knowledge Gaps</h3>
                {analytics.knowledge_gaps.length === 0 ? <p style={{ opacity: 0.65 }}>No knowledge gaps detected.</p> : (
                  <div style={{ display: 'grid', gap: '10px' }}>
                    {analytics.knowledge_gaps.map((gap, index) => (
                      <div key={`${gap.query}-${index}`} style={{ padding: '12px', borderRadius: '10px', background: 'rgba(100, 116, 139, 0.06)' }}>
                        <div style={{ fontWeight: 600, marginBottom: '7px' }}>{gap.query}</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', fontSize: '12px', opacity: 0.75 }}>
                          <span>Domain: {gap.domain}</span><span>Occurrences: {gap.occurrences}</span><span>Low confidence: {gap.low_confidence_count}</span><span>Unanswered: {gap.unanswered_count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="process-card card-panel">

              <div className="process-header">

                <p className="eyebrow">Workflow</p>

                <h2>How it works</h2>

              </div>

              <div className="process-flow">

                <span>Upload</span>

                <span className="arrow">→</span>

                <span>Process</span>

                <span className="arrow">→</span>

                <span>Embed</span>

                <span className="arrow">→</span>

                <span>Retrieve</span>

                <span className="arrow">→</span>

                <span>Answer</span>

              </div>

            </div>

          </div>

        </section>



        <section className="page-section ask-section" ref={(el) => { sectionRefs.current[1] = el; }}>

          <div className="section-inner">

            <div className="section-topbar">

              <div>

                <p className="eyebrow">AI Assistant</p>

                <h2>Ask AI</h2>

              </div>

            </div>



            <AskAI

              question={question}

              setQuestion={setQuestion}

              onAsk={handleAsk}

              loading={isSearching}

              results={results}

              emptyMessage={emptyMessage}

              isEmptyState={!isSearching && results.length === 0 && !emptyMessage}

              errorMessage={uploadState.type === 'error' && uploadState.message ? uploadState.message : ''}

              answerDetails={answerDetails}

              clarificationState={clarificationState}

              selectedTopK={selectedTopK}

              setSelectedTopK={setSelectedTopK}

              voiceState={voiceState}

              onVoiceStart={handleVoiceStart}

              onVoiceStop={handleVoiceStop}

              onSpeakAnswer={handleSpeakAnswer}

              onPauseSpeech={handleSpeechPause}

              onResumeSpeech={handleSpeechResume}

              onStopSpeech={handleSpeechStop}

            />

          </div>

        </section>



        <section className="page-section knowledge-section" ref={(el) => { sectionRefs.current[2] = el; }}>

          <div className="section-inner">

            <div className="section-topbar">

              <div>

                <p className="eyebrow">Repository</p>

                <h2>Knowledge Base</h2>

              </div>

            </div>



            <UploadCard

              onUpload={handleUpload}

              isUploading={isUploading}

              uploadState={uploadState}

              selectedFile={selectedFile}

              setSelectedFile={setSelectedFile}

            />



            <div className="documents-panel card-panel">

              <div className="panel-header">

                <h3>Uploaded Documents</h3>

              </div>



              <div className="table-wrap">

                <table>

                  <thead>

                    <tr>

                      <th>File name</th>

                      <th>Type</th>

                      <th>Chunks</th>

                      <th>Status</th>

                      <th>Source</th>

                    </tr>

                  </thead>

                  <tbody>

                    {uploadedDocuments.map((doc) => (

                      <tr key={doc.name}>

                        <td>{doc.name}</td>

                        <td>{doc.type}</td>

                        <td>{doc.chunks ?? 0}</td>

                        <td><span className="status-pill indexed">{doc.status}</span></td>

                        <td>{doc.source || 'Uploaded file'}</td>

                      </tr>

                    ))}

                  </tbody>

                </table>

              </div>

            </div>

          </div>

        </section>



        <section className="page-section history-section" ref={(el) => { sectionRefs.current[3] = el; }}>

          <div className="section-inner">

            <div className="section-topbar">

              <div>

                <p className="eyebrow">Activity</p>

                <h2>Search History</h2>

              </div>

            </div>



            <SearchHistory searches={searchHistory} onSelect={handleSelectQuestion} />

          </div>

        </section>



        <section className="page-section settings-section" ref={(el) => { sectionRefs.current[4] = el; }}>

          <div className="section-inner settings-inner">

            <div className="section-topbar">

              <div>

                <p className="eyebrow">Preferences</p>

                <h2>Settings</h2>

              </div>

            </div>



            <div className="settings-grid">

              <div className="settings-card card-panel">

                <h3>Appearance</h3>

                <div className="toggle-row">

                  <label className="toggle-option">

                    <input

                      type="radio"

                      name="theme"

                      checked={theme === 'light'}

                      onChange={() => setTheme('light')}

                    />

                    <span>Light mode</span>

                  </label>

                  <label className="toggle-option">

                    <input

                      type="radio"

                      name="theme"

                      checked={theme === 'dark'}

                      onChange={() => setTheme('dark')}

                    />

                    <span>Dark mode</span>

                  </label>

                </div>

              </div>



              <div className="settings-card card-panel">

                <h3>Data</h3>

                <button

                  type="button"

                  className="secondary-button full-width"

                  onClick={() => {

                    setSearchHistory([]);

                    localStorage.removeItem('ai-knowledge-searches');

                  }}

                >

                  Clear Search History

                </button>

              </div>



              <div className="settings-card card-panel">

                <h3>About Project</h3>

                <p className="settings-name">AI Knowledge Retrieval Platform</p>

                <p className="settings-description">

                  Intelligent document search and question answering system built for document-based knowledge retrieval.

                </p>

              </div>



              <div className="settings-card card-panel">

                <h3>Technology Stack</h3>

                <ul className="settings-list">

                  <li>React + Vite</li>

                  <li>Flask API</li>

                  <li>Sentence Transformers</li>

                  <li>ChromaDB</li>

                </ul>

              </div>

            </div>

          </div>

        </section>

      </div>

    </div>

  );

}



export default App;
