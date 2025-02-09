import React, { useState } from 'react';

function App() {
  const [file, setFile] = useState(null);
  const [requirements, setRequirements] = useState('');
  const [role, setRole] = useState('general');  // New role state
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => setFile(e.target.files[0]);
  const handleRequirementsChange = (e) => setRequirements(e.target.value);
  const handleRoleChange = (e) => setRole(e.target.value);  // Handle role selection

  const handleAnalyze = async () => {
    if (!file || !requirements) {
      alert("Please upload a file and enter requirements.");
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('requirements', requirements);
    formData.append('role', role);  // Pass role to the backend

    try {
      const response = await fetch('http://localhost:8000/analyze-resume/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to analyze resume.");
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error:", error);
      alert("An error occurred while analyzing the resume.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Resume Analyzer</h1>
      
      <label>
        <strong>Upload Resume (PDF):</strong>
        <input type="file" onChange={handleFileChange} style={{ display: 'block', margin: '10px 0' }} />
      </label>
      
      <label>
        <strong>Job Requirements (comma-separated):</strong>
        <textarea
          placeholder="Enter job requirements here..."
          value={requirements}
          onChange={handleRequirementsChange}
          style={{ display: 'block', width: '100%', height: '100px', margin: '10px 0' }}
        />
      </label>
      
      <label>
        <strong>Select Job Role:</strong>
        <select value={role} onChange={handleRoleChange} style={{ display: 'block', margin: '10px 0' }}>
          <option value="general">General</option>
          <option value="teacher">Teacher</option>
          <option value="admin">Admin</option>
          <option value="it_support">IT Support</option>
        </select>
      </label>
      
      <button onClick={handleAnalyze} disabled={loading} style={{ marginTop: '10px' }}>
        {loading ? 'Analyzing...' : 'Analyze'}
      </button>
      
      {loading && <p>Loading... Please wait.</p>}
      
      {result && (
        <div style={{ marginTop: '20px' }}>
          <h2>Analysis Result</h2>
          <p><strong>Best Match:</strong> {result.best_match}</p>
          <h3>Scores:</h3>
          <ul>
            {Object.entries(result.scores).map(([label, score]) => (
              <li key={label}><strong>{label}:</strong> {score}%</li>
            ))}
          </ul>
          <h3>Extracted Text (Preview):</h3>
          <pre style={{ whiteSpace: 'pre-wrap', background: '#f4f4f4', padding: '10px' }}>
            {result.extracted_text}
          </pre>
          <h3>Filtered Relevant Text (Preview):</h3>
          <pre style={{ whiteSpace: 'pre-wrap', background: '#f4f4f4', padding: '10px' }}>
            {result.filtered_text}
          </pre>
        </div>
      )}
    </div>
  );
}

export default App;
