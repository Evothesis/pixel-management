import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import ClientList from './pages/ClientList';
import ClientForm from './pages/ClientForm';
import UserGuide from './pages/UserGuide';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>Evothesis Pixel Management</h1>
          <nav>
            <a href="/">Dashboard</a>
            <a href="/clients">Clients</a>
            <a href="/guide">User Guide</a>
          </nav>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/clients" element={<ClientList />} />
            <Route path="/clients/new" element={<ClientForm />} />
            <Route path="/clients/:clientId/edit" element={<ClientForm />} />
            <Route path="/guide" element={<UserGuide />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;