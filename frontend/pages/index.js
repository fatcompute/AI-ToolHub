import { useState, useEffect } from 'react';
import Head from 'next/head';

export default function Home() {
  // State for the chat functionality
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // State for the code generation functionality
  const [codePrompt, setCodePrompt] = useState('');
  const [generatedCode, setGeneratedCode] = useState('');
  const [isGeneratingCode, setIsGeneratingCode] = useState(false);
  const [codeError, setCodeError] = useState('');


  useEffect(() => {
    const fetchModels = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/v1/models');
        if (!res.ok) {
          const errorData = await res.json();
          throw new Error(errorData.error || 'Failed to fetch models');
        }
        const data = await res.json();
        setModels(data.models || []);
        if (data.models && data.models.length > 0) {
          setSelectedModel(data.models[0]);
        }
      } catch (err) {
        setError(`Error fetching models: ${err.message}`);
      }
    };
    fetchModels();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) {
      setError('Please enter a prompt.');
      return;
    }
    if (!selectedModel) {
      setError('Please select a model.');
      return;
    }

    setIsLoading(true);
    setError('');
    setResponse('');

    try {
      const res = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model: selectedModel, prompt }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'An error occurred during the request.');
      }

      setResponse(data.response);
    } catch (err) {
      setError(`Error getting response: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCodeSubmit = async (e) => {
    e.preventDefault();
    if (!codePrompt.trim()) {
      setCodeError('Please enter a code generation prompt.');
      return;
    }
    if (!selectedModel) {
      setCodeError('Please select a model.');
      return;
    }

    setIsGeneratingCode(true);
    setCodeError('');
    setGeneratedCode('');

    try {
      const res = await fetch('http://localhost:8000/api/v1/generate/code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model: selectedModel, prompt: codePrompt }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'An error occurred during code generation.');
      }

      setGeneratedCode(data.code);
    } catch (err) {
      setCodeError(`Error generating code: ${err.message}`);
    } finally {
      setIsGeneratingCode(false);
    }
  };

  return (
    <div className="bg-gray-900 text-white min-h-screen font-sans">
      <Head>
        <title>AI Toolkit</title>
        <meta name="description" content="AI Toolkit Dashboard" />
      </Head>

      <main className="container mx-auto p-4 md:p-8">
        <header className="text-center mb-10">
          <h1 className="text-5xl font-bold text-cyan-400">AI Toolkit</h1>
          <p className="text-gray-400 mt-2">Your local AI-powered development environment</p>
        </header>

        {/* Model Selector */}
        <div className="max-w-md mx-auto mb-10">
          <label htmlFor="model-select" className="block text-sm font-medium text-gray-300 mb-2 text-center">
            Select Active Model
          </label>
          <select
            id="model-select"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="w-full bg-gray-700 border-gray-600 rounded-md p-2 focus:ring-cyan-500 focus:border-cyan-500"
            disabled={models.length === 0}
          >
            {models.length > 0 ? (
              models.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))
            ) : (
              <option>No models found...</option>
            )}
          </select>
        </div>

        {/* Chat Section */}
        <div className="bg-gray-800 rounded-xl shadow-lg p-6 mb-12">
          <h2 className="text-3xl font-bold text-gray-200 mb-4 text-center">Chat</h2>
          {error && (
            <div className="bg-red-500/20 border border-red-500 text-red-300 p-3 rounded-lg mb-4">
              <p>{error}</p>
            </div>
          )}
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <textarea
                rows="4"
                className="w-full bg-gray-700 border-gray-600 rounded-md p-2 focus:ring-cyan-500 focus:border-cyan-500"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g., Explain quantum computing in simple terms"
              />
            </div>
            <div className="text-center">
              <button
                type="submit"
                className="bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-2 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isLoading}
              >
                {isLoading ? 'Thinking...' : 'Send'}
              </button>
            </div>
          </form>
          {response && (
            <div className="mt-6 pt-4 border-t border-gray-700">
              <h3 className="text-xl font-semibold text-gray-200 mb-2">Response</h3>
              <div className="bg-gray-900/50 rounded-lg p-4">
                <pre className="whitespace-pre-wrap text-gray-300">{response}</pre>
              </div>
            </div>
          )}
        </div>

        {/* Code Generation Section */}
        <div className="bg-gray-800 rounded-xl shadow-lg p-6">
          <h2 className="text-3xl font-bold text-gray-200 mb-4 text-center">Code Development Preview</h2>
          {codeError && (
            <div className="bg-red-500/20 border border-red-500 text-red-300 p-3 rounded-lg mb-4">
              <p>{codeError}</p>
            </div>
          )}
          <form onSubmit={handleCodeSubmit}>
            <div className="mb-4">
              <textarea
                rows="3"
                className="w-full bg-gray-700 border-gray-600 rounded-md p-2 focus:ring-cyan-500 focus:border-cyan-500"
                value={codePrompt}
                onChange={(e) => setCodePrompt(e.target.value)}
                placeholder="e.g., A simple toggle button that changes color"
              />
            </div>
            <div className="text-center">
              <button
                type="submit"
                className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isGeneratingCode}
              >
                {isGeneratingCode ? 'Building...' : 'Generate Code'}
              </button>
            </div>
          </form>

          {generatedCode && (
            <div className="mt-6 pt-4 border-t border-gray-700 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-xl font-semibold text-gray-200 mb-2">Generated Code</h3>
                <div className="bg-gray-900/50 rounded-lg p-4 h-96 overflow-auto">
                  <pre className="whitespace-pre-wrap text-sm text-gray-300">{generatedCode}</pre>
                </div>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-200 mb-2">Live Preview</h3>
                <iframe
                  srcDoc={generatedCode}
                  title="Code Preview"
                  className="w-full h-96 bg-white rounded-lg border-4 border-gray-700"
                  sandbox="allow-scripts"
                />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
