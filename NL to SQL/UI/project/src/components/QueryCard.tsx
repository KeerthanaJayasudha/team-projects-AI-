import { useState } from 'react';

interface QueryCardProps {
  onRunQuery: (query: string) => void;
  onClear: () => void;
  isConfigured: boolean;
}

function QueryCard({ onRunQuery, onClear, isConfigured }: QueryCardProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onRunQuery(query);
    }
  };

  const handleClear = () => {
    setQuery('');
    onClear();
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Ask a question
      </h2>

      {!isConfigured && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            💡 Configure your database to run queries.
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., show all customers"
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
        />

        <button
          type="submit"
          disabled={!isConfigured}
          title={!isConfigured ? 'Configure database to run queries' : undefined}
          className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors"
        >
          Run Query
        </button>

        <button
          type="button"
          onClick={handleClear}
          className="px-6 py-2 bg-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-300"
        >
          Clear
        </button>
      </form>
    </div>
  );
}

export default QueryCard;
