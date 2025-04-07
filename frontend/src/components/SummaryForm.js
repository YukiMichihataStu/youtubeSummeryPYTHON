import React, { useState } from 'react';
import axios from 'axios';

// スタイル選択肢
const SUMMARY_STYLES = [
  { value: 'bullet', label: '箇条書き' },
  { value: 'paragraph', label: '説明文' },
  { value: 'gal', label: 'ギャル口調' },
  { value: 'oneesan', label: 'おねーさん口調' },
];

const SummaryForm = () => {
  const [url, setUrl] = useState('');
  const [style, setStyle] = useState('bullet');
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/summarize', {
        params: { url, style }
      });
      setSummary(response.data.summary);
    } catch (err) {
      setError(err.response?.data?.detail || '要約の取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="summary-form">
      <h2>YouTube動画を要約</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="url">YouTube URL:</label>
          <input
            id="url"
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="style">要約スタイル:</label>
          <select
            id="style"
            value={style}
            onChange={(e) => setStyle(e.target.value)}
          >
            {SUMMARY_STYLES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        
        <button type="submit" disabled={loading}>
          {loading ? '要約中...' : '要約する'}
        </button>
      </form>
      
      {error && <div className="error">{error}</div>}
      
      {summary && (
        <div className="summary-result">
          <h3>要約結果:</h3>
          <div className="summary-content">
            {summary.split('\n').map((line, i) => (
              <p key={i}>{line}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SummaryForm;
