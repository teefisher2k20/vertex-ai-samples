import React, { useState, useEffect } from 'react';
import { NotebookCard } from '@/components/NotebookCard/NotebookCard';
import { searchNotebooks } from '@/api/client';
import { Notebook, SearchResult } from '@/types/notebook';
import { Search, Loader2 } from 'lucide-react';

const HomePage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (searchQuery: string) => {
    setLoading(true);
    try {
      // In a real app, we'd pass actual filters
      const data = await searchNotebooks(searchQuery, {});
      setResults(data);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    handleSearch('');
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <img 
                src="https://www.gstatic.com/images/branding/product/1x/vertex_ai_48dp.png" 
                alt="Vertex AI" 
                className="h-8 w-8 mr-3"
              />
              <h1 className="text-xl font-semibold text-gray-900">Vertex AI Samples</h1>
            </div>
            <div className="flex-1 max-w-2xl mx-8">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-gray-50 placeholder-gray-500 focus:outline-none focus:bg-white focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Search notebooks (e.g., 'automl image classification')..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch(query)}
                />
              </div>
            </div>
            <div>
              <a 
                href="https://github.com/GoogleCloudPlatform/vertex-ai-samples"
                className="text-gray-500 hover:text-gray-700"
                target="_blank"
                rel="noopener noreferrer"
              >
                GitHub
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {results?.notebooks.map((notebook) => (
              <NotebookCard 
                key={notebook.id} 
                notebook={notebook} 
                onClick={(n) => console.log('Clicked:', n.title)}
              />
            ))}
          </div>
        )}
        
        {!loading && results?.notebooks.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No notebooks found matching your criteria.</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default HomePage;
