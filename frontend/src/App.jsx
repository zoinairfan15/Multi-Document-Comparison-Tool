import { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = 'http://127.0.0.1:8000';

function renderFormatted(text) {
  const lines = text.split('\n').filter((l) => l.trim() !== '');
  return lines.map((line, i) => {
    if (line.startsWith('### ')) {
      return (
        <h4 key={i} className="result-heading">
          {line.replace('### ', '').replace(/\*\*/g, '')}
        </h4>
      );
    }
    const parts = line.split(/(\*\*[^*]+\*\*)/g).map((part, j) =>
      part.startsWith('**') && part.endsWith('**') ? (
        <strong key={j}>{part.slice(2, -2)}</strong>
      ) : (
        part
      )
    );
    return (
      <p key={i} className="result-line">
        {parts}
      </p>
    );
  });
}

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [papers, setPapers] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [compareQuery, setCompareQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [faithfulness, setFaithfulness] = useState('');
  const [loading, setLoading] = useState(false);
  const [ingested, setIngested] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [embeddingPoints, setEmbeddingPoints] = useState(null);
  const [sources, setSources] = useState(null);
const [sourceTitles, setSourceTitles] = useState({});
const [activeSourcePaper, setActiveSourcePaper] = useState(null);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/search`, {
        query: searchQuery,
        max_results: 5,
      });
      setPapers(res.data.papers);
      setSelectedIds([]);
      setIngested(false);
    } catch (err) {
      alert('Search failed: ' + err.message);
    }
    setLoading(false);
  };

  const handleUpload = async (e) => {
  const files = Array.from(e.target.files);
  if (files.length === 0) return;

  setUploading(true);
  try {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const res = await axios.post(`${API_BASE}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    const newPapers = res.data.papers.map((p) => ({
      id: p.id,
      title: p.title,
      summary: 'Uploaded document',
      pdf_url: null,
    }));

    setPapers((prev) => [...prev, ...newPapers]);
    setSelectedIds((prev) => [...prev, ...newPapers.map((p) => p.id)]);
    setIngested(true);
  } catch (err) {
    alert('Upload failed: ' + err.message);
  }
  setUploading(false);
  e.target.value = '';
};

  const toggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleIngest = async () => {
    if (selectedIds.length < 2) {
      alert('Select at least 2 papers to compare');
      return;
    }
    setLoading(true);
    try {
      const papers_meta = {};
      papers.forEach((p) => {
        if (selectedIds.includes(p.id)) {
          papers_meta[p.id] = { title: p.title, pdf_url: p.pdf_url };
        }
      });
      await axios.post(`${API_BASE}/ingest`, {
        paper_ids: selectedIds,
        papers_meta,
      });
      setIngested(true);
    } catch (err) {
      alert('Ingest failed: ' + err.message);
    }
    setLoading(false);
  };

  const handleCompare = async () => {
    setLoading(true);
    setAnswer('');
     setFaithfulness('');
     setMetrics(null);
     setSources(null);
     setActiveSourcePaper(null);
    try {
      const res = await axios.post(`${API_BASE}/compare`, {
        query: compareQuery,
        paper_ids: selectedIds,
      });
     setAnswer(res.data.answer);
     setFaithfulness(res.data.faithfulness);
     setMetrics(res.data.metrics);
     setSources(res.data.sources);
     setSourceTitles(res.data.titles);
     setActiveSourcePaper(null);
    } catch (err) {
      alert('Compare failed: ' + err.message);
    }
    setLoading(false);
  };
  const handleDownload = () => {
  if (!answer) return;

  const selectedTitles = selectedIds.map((id) => papers.find((p) => p.id === id)?.title || id);

  let report = `# Multi-Document Comparison Report\n\n`;
  report += `**Query:** ${compareQuery}\n\n`;
  report += `**Papers compared:**\n`;
  selectedTitles.forEach((t) => (report += `- ${t}\n`));
  report += `\n---\n\n## Comparison\n\n${answer}\n\n`;

  if (faithfulness) {
    report += `---\n\n## Faithfulness Check\n\n${faithfulness}\n\n`;
  }

  if (metrics) {
    report += `---\n\n## Evaluation Metrics\n\n`;
    report += `- Average relevance score: ${metrics.avg_relevance_score}\n`;
    report += `- Retrieval time: ${metrics.retrieval_time_sec}s\n`;
    report += `- Generation time: ${metrics.generation_time_sec}s\n`;
    report += `- Faithfulness rating: ${metrics.faithfulness_rating}\n`;
    report += `- Chunks used: ${metrics.chunks_retrieved}\n`;
  }

  const blob = new Blob([report], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'comparison-report.md';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};
  const handleVisualize = async () => {
  try {
    const res = await axios.post(`${API_BASE}/visualize`, {
      paper_ids: selectedIds,
    });
    setEmbeddingPoints(res.data.points);
  } catch (err) {
    alert('Visualization failed: ' + err.message);
  }
};

  return (
    <div className="page">
      <p className="eyebrow">Research Assistant</p>
      <h1 className="title">Multi-Document Comparison Tool</h1>
      <p className="subtitle">
        Search arXiv, select papers, and get a citation-grounded comparison of
        their methods, findings, and contributions.
      </p>

      <div className="step">
        <div className="step-label">
          <span className="step-number">01</span>
          <h2 className="step-title">Search arXiv</h2>
        </div>
        <div className="input-row">
          <input
            className="text-input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="e.g. transformer efficiency"
          />
          <button className="btn" onClick={handleSearch} disabled={loading}>
            Search
          </button>
        </div>
      </div>

      <div className="step">
  <div className="step-label">
    <span className="step-number">01b</span>
    <h2 className="step-title">Or upload your own PDFs</h2>
  </div>
  <input
    type="file"
    accept="application/pdf"
    multiple
    onChange={handleUpload}
    disabled={uploading}
    className="text-input"
    style={{ padding: 10 }}
  />
  {uploading && (
    <div className="spinner-row" style={{ marginTop: 10 }}>
      <div className="spinner" />
      <span>Processing upload...</span>
    </div>
  )}
</div>

      {papers.length > 0 && (
        <div className="step">
          <div className="step-label">
            <span className="step-number">02</span>
            <h2 className="step-title">Select papers to compare</h2>
          </div>
          <div className="paper-list">
            {papers.map((p) => (
              <div
                key={p.id}
                className={`paper-card ${selectedIds.includes(p.id) ? 'selected' : ''}`}
                onClick={() => toggleSelect(p.id)}
              >
                <div className="paper-card-top">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(p.id)}
                    onChange={() => toggleSelect(p.id)}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <p className="paper-title">{p.title}</p>
                </div>
                <p className="paper-summary">{p.summary.slice(0, 150)}...</p>
              </div>
            ))}
          </div>
          <button
            className="btn"
            onClick={handleIngest}
            disabled={loading || selectedIds.length < 2}
          >
            Ingest Selected ({selectedIds.length})
          </button>
          {ingested && <span className="ingested-badge">✓ Ingested</span>}
        </div>
      )}

      {ingested && (
        <div className="step">
          <div className="step-label">
            <span className="step-number">03</span>
            <h2 className="step-title">Ask a comparison question</h2>
          </div>
          <div className="input-row">
            <input
              className="text-input"
              value={compareQuery}
              onChange={(e) => setCompareQuery(e.target.value)}
              placeholder="e.g. What method do they propose?"
            />
            <button className="btn" onClick={handleCompare} disabled={loading}>
              Compare
            </button>
            <button className="btn" onClick={handleVisualize} style={{ marginLeft: 8, background: 'var(--surface-2)', color: 'var(--text)' }}>
  Visualize Embeddings
</button>
          </div>
        </div>
      )}

      {loading && (
        <div className="spinner-row">
          <div className="spinner" />
          <span>Working on it...</span>
        </div>
      )}

     {answer && (
  <div className="result-card">
    <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
      <button
        className="btn"
        onClick={handleDownload}
        style={{ background: 'var(--surface-2)', color: 'var(--text)', fontSize: 12, padding: '8px 14px' }}
      >
        ⬇ Download Report (.md)
      </button>
    </div>
    {renderFormatted(answer)}
  </div>
)}
      {sources && (
  <div className="sources-toggle">
    {Object.keys(sources).map((pid) => (
      <button
        key={pid}
        className={`source-chip ${activeSourcePaper === pid ? 'active' : ''}`}
        onClick={() => setActiveSourcePaper(activeSourcePaper === pid ? null : pid)}
      >
        📄 {sourceTitles[pid]?.slice(0, 30) || pid}
      </button>
    ))}
  </div>
)}

{activeSourcePaper && sources && sources[activeSourcePaper] && (
  <div className="source-panel">
    <p className="metrics-label" style={{ margin: '0 0 10px' }}>
      Retrieved chunks from: {sourceTitles[activeSourcePaper]}
    </p>
    {sources[activeSourcePaper].map((chunk, i) => (
      <p key={i} className="source-chunk">{chunk.slice(0, 400)}...</p>
    ))}
  </div>
)}

      {faithfulness && (
        <div className="faithfulness-card">
          <p className="faithfulness-label">Faithfulness Check</p>
          <p className="faithfulness-text">{faithfulness}</p>
        </div>
      )}
      {metrics && (
  <div className="metrics-card">
    <p className="metrics-label">Evaluation Metrics</p>
    <div className="metrics-grid">
      <div className="metric">
        <span className="metric-value">{metrics.avg_relevance_score}</span>
        <span className="metric-name">Avg Relevance</span>
      </div>
      <div className="metric">
        <span className="metric-value">{metrics.retrieval_time_sec}s</span>
        <span className="metric-name">Retrieval Time</span>
      </div>
      <div className="metric">
        <span className="metric-value">{metrics.generation_time_sec}s</span>
        <span className="metric-name">Generation Time</span>
      </div>
      <div className="metric">
        <span className="metric-value">{metrics.faithfulness_rating}</span>
        <span className="metric-name">Faithfulness</span>
      </div>
      <div className="metric">
        <span className="metric-value">{metrics.chunks_retrieved}</span>
        <span className="metric-name">Chunks Used</span>
      </div>
    </div>
  </div>
)}
{embeddingPoints && (
  <div className="result-card" style={{ marginTop: 16 }}>
    <h4 className="result-heading">Chunk Embedding Space (PCA)</h4>
    <EmbeddingPlot
      points={embeddingPoints}
      paperTitles={Object.fromEntries(papers.map((p) => [p.id, p.title]))}
    />
  </div>
)}
    </div>
  );
}
const PAPER_COLORS = ['#c9a227', '#4f8f8a', '#b8544a', '#5a9d72', '#7a6fc4', '#c47a9e'];

function EmbeddingPlot({ points, paperTitles }) {
  if (!points || points.length === 0) return null;

  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const yMin = Math.min(...ys), yMax = Math.max(...ys);
  const pad = 30;
  const width = 600, height = 400;

  const scaleX = (x) => pad + ((x - xMin) / (xMax - xMin || 1)) * (width - 2 * pad);
  const scaleY = (y) => height - pad - ((y - yMin) / (yMax - yMin || 1)) * (height - 2 * pad);

  const uniquePaperIds = [...new Set(points.map((p) => p.paper_id))];
  const colorMap = {};
  uniquePaperIds.forEach((pid, i) => {
    colorMap[pid] = PAPER_COLORS[i % PAPER_COLORS.length];
  });

  return (
    <div>
      <svg width={width} height={height} style={{ background: '#171a21', borderRadius: 8 }}>
        {points.map((p, i) => (
          <circle
            key={i}
            cx={scaleX(p.x)}
            cy={scaleY(p.y)}
            r={5}
            fill={colorMap[p.paper_id]}
            opacity={0.8}
          >
            <title>{p.preview}</title>
          </circle>
        ))}
      </svg>
      <div style={{ display: 'flex', gap: 16, marginTop: 10, flexWrap: 'wrap' }}>
        {uniquePaperIds.map((pid) => (
          <div key={pid} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: colorMap[pid] }} />
            <span style={{ fontSize: 12, color: '#8f94a3' }}>
              {paperTitles[pid]?.slice(0, 40) || pid}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;