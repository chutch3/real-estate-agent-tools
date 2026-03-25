import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles, Loader2, MapPin } from 'lucide-react';
import apiClient from '../apiClient';

const agentFields = [
  { label: 'Agent Name', key: 'agent_name', aria: 'Agent Name' },
  { label: 'Company', key: 'agent_company', aria: 'Company' },
  { label: 'Contact', key: 'agent_contact', aria: 'Contact' },
];

function GeneratePost() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const property = state?.property;

  const [agentInfo, setAgentInfo] = useState({
    agent_name: '',
    agent_company: '',
    agent_contact: '',
  });
  const [post, setPost] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    try {
      setIsLoading(true);
      setError('');
      const data = await apiClient.generatePost(property?.formatted_address, agentInfo, null);
      setPost(data.post);
    } catch (err) {
      setError('Failed to generate post. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main
      data-testid="generate-post-page"
      className="min-h-screen bg-linen-100 pt-14"
    >
      <div className="max-w-2xl mx-auto px-6 py-10">
        {/* Back */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 font-sans text-sm text-ink-400 hover:text-ink-900 transition-colors mb-8 group"
          aria-label="Go back"
        >
          <ArrowLeft size={14} className="group-hover:-translate-x-0.5 transition-transform" />
          Back
        </button>

        {/* Heading */}
        <div className="mb-8 animate-fade-up" style={{ animationFillMode: 'both' }}>
          <h1 className="font-serif text-4xl text-ink-900 mb-2">Generate Post</h1>
          {property && (
            <div className="flex items-center gap-2">
              <MapPin size={13} className="text-bronze-400" strokeWidth={1.5} />
              <span className="font-sans text-sm text-ink-400">
                {property.formatted_address}
              </span>
            </div>
          )}
        </div>

        {/* Agent form */}
        <section
          className="bg-white rounded-lg border border-linen-200 p-6 mb-6 animate-fade-up"
          style={{ animationDelay: '60ms', animationFillMode: 'both' }}
          aria-label="Agent information"
        >
          <h2 className="font-serif text-lg text-ink-700 mb-4">Agent Information</h2>
          <div className="space-y-4">
            {agentFields.map(({ label, key, aria }) => (
              <div key={key}>
                <label
                  htmlFor={`field-${key}`}
                  className="block font-sans text-xs uppercase tracking-widest text-ink-400 mb-1.5"
                >
                  {label}
                </label>
                <input
                  id={`field-${key}`}
                  type="text"
                  aria-label={aria}
                  value={agentInfo[key]}
                  onChange={(e) => setAgentInfo((prev) => ({ ...prev, [key]: e.target.value }))}
                  className="w-full px-3 py-2.5 border border-linen-300 rounded-md bg-white font-sans text-sm text-ink-900 placeholder-ink-300 focus:outline-none focus:border-bronze-400 transition-colors"
                />
              </div>
            ))}
          </div>
        </section>

        {/* Generate button */}
        <button
          onClick={handleGenerate}
          disabled={isLoading}
          className="flex items-center gap-2 bg-bronze-500 hover:bg-bronze-600 disabled:bg-linen-300 disabled:cursor-not-allowed text-white font-sans text-sm font-medium py-3 px-6 rounded-md transition-colors mb-5 focus:outline-none focus:ring-2 focus:ring-bronze-400 focus:ring-offset-1"
        >
          {isLoading ? (
            <Loader2 size={15} className="animate-spin" />
          ) : (
            <Sparkles size={15} strokeWidth={2} />
          )}
          {isLoading ? 'Generating…' : 'Generate'}
        </button>

        {error && (
          <p className="font-sans text-sm text-red-700 mb-5" role="alert">
            {error}
          </p>
        )}

        {/* Result */}
        {post && (
          <div
            className="bg-white rounded-lg border border-linen-200 p-5 animate-fade-up"
            style={{ animationFillMode: 'both' }}
          >
            <label
              htmlFor="post-output"
              className="block font-sans text-xs uppercase tracking-widest text-ink-400 mb-2"
            >
              Generated Post
            </label>
            <textarea
              id="post-output"
              value={post}
              onChange={(e) => setPost(e.target.value)}
              rows={8}
              className="w-full font-sans text-sm text-ink-800 leading-relaxed resize-none focus:outline-none"
              aria-label="Generated post content"
            />
          </div>
        )}
      </div>
    </main>
  );
}

export default GeneratePost;
