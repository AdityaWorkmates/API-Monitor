import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import EndpointList from './pages/EndpointList';
import EndpointDetails from './pages/EndpointDetails';
import AddEndpoint from './pages/AddEndpoint';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/endpoints" element={<EndpointList />} />
          <Route path="/endpoints/new" element={<AddEndpoint />} />
          <Route path="/endpoints/:id" element={<EndpointDetails />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;