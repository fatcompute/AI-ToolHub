import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Header from './components/Header';
import ModelManagement from './components/ModelManagement';
import FineTuning from './components/FineTuning';
import Evaluation from './components/Evaluation';
import CodeHealth from './components/CodeHealth';
import Home from './components/Home';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/models" element={<ModelManagement />} />
            <Route path="/finetune" element={<FineTuning />} />
            <Route path="/evaluate" element={<Evaluation />} />
            <Route path="/code-health" element={<CodeHealth />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
