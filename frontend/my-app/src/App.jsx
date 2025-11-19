import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [files, setFiles] = useState([]);
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [processedFiles, setProcessedFiles] = useState([]);

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
  };

  const handleIngest = async () => {
    if (files.length === 0) {
      alert('Please select files to upload');
      return;
    }

    setIngesting(true);
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await axios.post(`${API_BASE_URL}/ingest`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setProcessedFiles(response.data.processed_files);
      alert(`Successfully processed ${response.data.total_chunks} chunks from ${response.data.processed_files.length} files`);
    } catch (error) {
      console.error('Error ingesting documents:', error);
      alert('Error ingesting documents');
    } finally {
      setIngesting(false);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) {
      alert('Please enter a query');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/query`, {
        query: query,
        top_k: 3
      });
      setAnswer(response.data.answer);
      setSources(response.data.sources);
    } catch (error) {
      console.error('Error querying:', error);
      alert('Error processing query');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1> Context-Aware RAG Pipeline</h1>
        <p>Upload documents, ask questions, and get source-aware answers</p>
      </header>

      <div className="container">

        {/* Upload Section */}
        <section className="card">
          <h2>Upload Document </h2>
          <div className="upload-area">
            <input
              type="file"
              multiple
              accept=".pdf,.txt,.docx,.csv"
              onChange={handleFileChange}
              className="file-input"
            />
            <button 
              onClick={handleIngest} 
              disabled={ingesting}
              className="btn btn-primary"
            >
              {ingesting ? 'Processing...' : 'Ingest Documents'}
            </button>
          </div>

          {processedFiles.length > 0 && (
            <div className="processed-files">
              <h3>Processed Files:</h3>
              <ul>
                {processedFiles.map((file, index) => (
                  <li key={index}>{file}</li>
                ))}
              </ul>
            </div>
          )}
        </section>

        {/* Query Section */}
        <section className="card">
          <h2> Ask Questions</h2>
          <div>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your question here..."
              rows="4"
              className="query-textarea"
            />
            <button 
              onClick={handleQuery} 
              disabled={loading}
              className="btn btn-secondary"
            >
              {loading ? 'Searching...' : 'Ask Question'}
            </button>
          </div>
        </section>

        {/* Results */}
        {answer && (
          <section className="card">
            <h2> Answer</h2>
            <div className="answer-box">
              <p>{answer}</p>
            </div>

            {sources.length > 0 && (
              <div>
                <h3> Sources</h3>
                <div className="sources-list">
                  {sources.map((source, index) => (
                    <div key={index} className="source-card">
                      <div className="source-header">
                        <strong>{source.source_filename}</strong>
                        {source.page_number && (
                          <span className="page-badge">Page {source.page_number}</span>
                        )}
                        <span className="score-badge">
                          Score: {(source.score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <p className="source-content">{source.chunk_text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}

export default App;
