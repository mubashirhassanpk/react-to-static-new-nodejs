import React from 'react';

    function App() {
      return (
        <div style={{ padding: '20px', fontFamily: 'Arial', textAlign: 'center' }}>
          <h1 style={{ color: '#2563eb' }}>Test React App</h1>
          <p>This is a test build from the paste functionality.</p>
          <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#f3f4f6', borderRadius: '8px' }}>
            <h2>Features Tested:</h2>
            <ul style={{ textAlign: 'left', display: 'inline-block' }}>
              <li>✅ Paste code functionality</li>
              <li>✅ Build process automation</li>
              <li>✅ Status updates</li>
              <li>✅ Download and preview</li>
            </ul>
          </div>
        </div>
      );
    }

    export default App;