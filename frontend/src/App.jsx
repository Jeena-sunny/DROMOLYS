




import React, { useState, useEffect } from 'react';

const API_BASE = 'http://127.0.0.1:8000/api';

export default function App() {
  const [user, setUser] = useState(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [recordsData, setRecordsData] = useState({ records: [], total: 0, page: 1, pageSize: 10 });
  const [stats, setStats] = useState(null);
  const [histogram, setHistogram] = useState([]);
  const [vehicleFilter, setVehicleFilter] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');

  useEffect(() => {
    fetch(`${API_BASE}/auth/me`, { credentials: 'include' })
      .then(res => res.ok ? res.json() : null)
      .then(data => { if (data) { setUser(data); loadDatasets(); } });
  }, []);

  const loadDatasets = () => {
    fetch(`${API_BASE}/datasets`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => setDatasets(data));
  };

  const handleAuth = (e) => {
    e.preventDefault();
    const endpoint = isRegistering ? '/auth/register' : '/auth/login';
    fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
      credentials: 'include'
    }).then(res => res.json()).then(data => {
      if (data.userId || data.message) {
        setUser({ email });
        loadDatasets();
      } else {
        alert(data.error);
      }
    });
  };

  const handleLogout = () => {
    fetch(`${API_BASE}/auth/logout`, { method: 'POST', credentials: 'include' })
      .then(() => { setUser(null); setSelectedDataset(null); setDatasets([]); });
  };

  const handleUpload = (e) => {
    e.preventDefault();
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append('file', selectedFile);
    setUploadStatus('Uploading & validating...');

    fetch(`${API_BASE}/datasets/upload`, {
      method: 'POST',
      body: formData,
      credentials: 'include'
    }).then(res => res.json()).then(data => {
      if (data.datasetId) {
        setUploadStatus('Upload successful!');
        loadDatasets();
        setSelectedFile(null);
      } else {
        setUploadStatus('Error: ' + data.error);
      }
    });
  };

  const openDataset = (ds) => {
    setSelectedDataset(ds);
    loadDatasetDetails(ds.id, 1, vehicleFilter);
  };

  const loadDatasetDetails = (id, page = 1, vClass = '') => {
    let url = `${API_BASE}/datasets/${id}/records?page=${page}&pageSize=10`;
    if (vClass) url += `&vehicleClass=${vClass}`;

    fetch(url, { credentials: 'include' })
      .then(res => res.json())
      .then(data => setRecordsData(data));

    let statUrl = `${API_BASE}/datasets/${id}/statistics`;
    if (vClass) statUrl += `?vehicleClass=${vClass}`;
    fetch(statUrl, { credentials: 'include' })
      .then(res => res.json())
      .then(data => setStats(data));

    fetch(`${API_BASE}/datasets/${id}/histogram`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => setHistogram(data));
  };

  if (!user) {
    return (
      <div style={{ maxWidth: '400px', margin: '80px auto', padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
        <h2>{isRegistering ? 'Register' : 'Login'} - DromoLys Platform</h2>
        <form onSubmit={handleAuth}>
          <div style={{ marginBottom: '10px' }}>
            <label>Email:</label><br/>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required style={{ width: '100%', padding: '8px' }} />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label>Password:</label><br/>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required style={{ width: '100%', padding: '8px' }} />
          </div>
          <button type="submit" style={{ width: '100%', padding: '10px', background: '#007BFF', color: '#fff', border: 'none', borderRadius: '4px' }}>
            {isRegistering ? 'Sign Up' : 'Log In'}
          </button>
        </form>
        <p style={{ marginTop: '15px', textAlign: 'center' }}>
          {isRegistering ? 'Already have an account?' : "Don't have an account?"}{' '}
          <span style={{ color: '#007BFF', cursor: 'pointer' }} onClick={() => setIsRegistering(!isRegistering)}>
            {isRegistering ? 'Log In' : 'Sign Up'}
          </span>
        </p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #ddd', paddingBottom: '10px' }}>
        <h2>DromoLys Vehicle Observation Dashboard</h2>
        <div>
          <span>Welcome, <b>{user.email}</b></span>
          <button onClick={handleLogout} style={{ marginLeft: '15px', padding: '5px 10px' }}>Logout</button>
        </div>
      </header>

      {!selectedDataset ? (
        <div style={{ marginTop: '20px' }}>
          <h3>Upload CSV Dataset</h3>
          <form onSubmit={handleUpload} style={{ marginBottom: '30px', padding: '15px', background: '#f9f9f9', borderRadius: '5px' }}>
            <input type="file" accept=".csv" onChange={e => setSelectedFile(e.target.files[0])} />
            <button type="submit" style={{ marginLeft: '10px', padding: '6px 12px' }}>Upload & Import</button>
            <p style={{ color: 'green', marginTop: '5px' }}>{uploadStatus}</p>
          </form>

          <h3>Your Uploaded Datasets</h3>
          <table border="1" cellPadding="8" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#eee' }}>
                <th>Filename</th>
                <th>Records</th>
                <th>Status</th>
                <th>Upload Date</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {datasets.map(ds => (
                <tr key={ds.id}>
                  <td>{ds.filename}</td>
                  <td>{ds.record_count}</td>
                  <td><b>{ds.status}</b></td>
                  <td>{ds.created_at}</td>
                  <td>
                    <button onClick={() => openDataset(ds)} disabled={ds.status !== 'completed'}>View Analytics</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div style={{ marginTop: '20px' }}>
          <button onClick={() => setSelectedDataset(null)} style={{ marginBottom: '15px' }}>← Back to Datasets</button>
          <h3>Dataset: {selectedDataset.filename}</h3>

          <div style={{ display: 'flex', gap: '20px' }}>
            {/* Main Table & Filters */}
            <div style={{ flex: 2 }}>
              <div style={{ marginBottom: '10px' }}>
                <label>Filter Vehicle Class: </label>
                <input type="text" value={vehicleFilter} onChange={e => { setVehicleFilter(e.target.value); loadDatasetDetails(selectedDataset.id, 1, e.target.value); }} placeholder="e.g. Car, Bus" style={{ padding: '5px' }} />
              </div>

              <table border="1" cellPadding="6" style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: '#eee' }}>
                    <th>Time</th>
                    <th>Vehicle Class</th>
                    <th>X (px)</th>
                    <th>Y (px)</th>
                  </tr>
                </thead>
                <tbody>
                  {recordsData.records.map((r, idx) => (
                    <tr key={idx}>
                      <td>{r.time}</td>
                      <td>{r.vehicle_class}</td>
                      <td>{r['x(px)']}</td>
                      <td>{r['y(px)']}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div style={{ marginTop: '10px', display: 'flex', gap: '10px', alignItems: 'center' }}>
                <button disabled={recordsData.page <= 1} onClick={() => loadDatasetDetails(selectedDataset.id, recordsData.page - 1, vehicleFilter)}>Previous</button>
                <span>Page {recordsData.page} of {Math.ceil(recordsData.total / recordsData.pageSize) || 1}</span>
                <button disabled={recordsData.page * recordsData.pageSize >= recordsData.total} onClick={() => loadDatasetDetails(selectedDataset.id, recordsData.page + 1, vehicleFilter)}>Next</button>
              </div>
            </div>

            {/* Sidebar Statistics & Histogram */}
            <div style={{ flex: 1, background: '#f4f4f4', padding: '15px', borderRadius: '5px' }}>
              <h4>Summary Statistics</h4>
              {stats ? (
                <div>
                  <p><b>Total Count:</b> {stats.count}</p>
                  <h5>X Coordinate (px):</h5>
                  <ul>
                    <li>Min: {stats['x(px)']?.min}</li>
                    <li>Median: {stats['x(px)']?.median}</li>
                    <li>Max: {stats['x(px)']?.max}</li>
                  </ul>
                  <h5>Y Coordinate (px):</h5>
                  <ul>
                    <li>Min: {stats['y(px)']?.min}</li>
                    <li>Median: {stats['y(px)']?.median}</li>
                    <li>Max: {stats['y(px)']?.max}</li>
                  </ul>
                </div>
              ) : <p>Loading stats...</p>}

              <h4>Observations Histogram (by Hour)</h4>
              <ul>
                {histogram.map((h, i) => (
                  <li key={i}>Hour {h.hour_bin}:00 → {h.count} observations</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}







