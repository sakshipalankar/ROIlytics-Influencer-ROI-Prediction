import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { predictBatch } from '../../api/client';
import { Upload, Download, FileText } from 'lucide-react';

const BatchUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1,
    onDrop: (accepted) => {
      setFile(accepted[0] ?? null);
      setResultUrl(null);
      setError(null);
    },
  });

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const blob = await predictBatch(file);
      const url = URL.createObjectURL(blob);
      setResultUrl(url);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div
        {...getRootProps()}
        className={`dropzone${isDragActive ? ' active' : ''}`}
        id="batch-dropzone"
      >
        <input {...getInputProps()} id="batch-file-input" />
        <div className="dropzone-icon">📂</div>
        {file ? (
          <>
            <div className="dropzone-text" style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'center' }}>
              <FileText size={16} /> {file.name}
            </div>
            <div className="dropzone-hint">{(file.size / 1024).toFixed(1)} KB — click to replace</div>
          </>
        ) : (
          <>
            <div className="dropzone-text">Drop your CSV file here, or click to browse</div>
            <div className="dropzone-hint">Required columns: followers_count, media_count, avg_likes, avg_comments, category, posting_frequency, spend</div>
          </>
        )}
      </div>

      {file && (
        <button
          id="batch-upload-btn"
          className="btn btn-primary"
          onClick={handleUpload}
          disabled={loading}
        >
          {loading ? (
            <><div className="spinner" style={{ width: 16, height: 16 }} /> Processing…</>
          ) : (
            <><Upload size={16} /> Run Batch Predictions</>
          )}
        </button>
      )}

      {error && <div className="alert alert-error">⚠️ {error}</div>}

      {resultUrl && (
        <a
          id="batch-download-link"
          href={resultUrl}
          download="roi_predictions.csv"
          className="btn btn-secondary"
          style={{ justifyContent: 'center' }}
        >
          <Download size={16} /> Download Results CSV
        </a>
      )}

      <div className="alert alert-info" style={{ fontSize: 12 }}>
        💡 You can export the sample data from the Data Explorer page to get a template CSV.
      </div>
    </div>
  );
};

export default BatchUpload;
