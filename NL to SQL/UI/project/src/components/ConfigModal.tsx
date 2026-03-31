import { useState, useEffect } from 'react';
import { X } from 'lucide-react';

interface ConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (config: DatabaseConfig) => void;
}

export interface DatabaseConfig {
  category: 'Structured' | 'Unstructured' | '';
  type: string;
  credentials: Record<string, string>;
}

function ConfigModal({ isOpen, onClose, onSave }: ConfigModalProps) {
  const [category, setCategory] = useState<'Structured' | 'Unstructured' | ''>('');
  const [type, setType] = useState('');
  const [credentials, setCredentials] = useState<Record<string, string>>({});

  const structuredTypes = ['PostgreSQL', 'MySQL', 'SQLite', 'SQL Server'];
  const unstructuredTypes = ['MongoDB', 'Cassandra', 'CouchDB'];

  useEffect(() => {
    setType('');
    setCredentials({});
  }, [category]);

  useEffect(() => {
    setCredentials({});
  }, [type]);

  const getCredentialFields = () => {
    if (type === 'PostgreSQL' || type === 'MySQL') {
      return ['Host', 'Port', 'Username', 'Password', 'Database'];
    } else if (type === 'SQLite') {
      return ['File Path'];
    } else if (type === 'MongoDB') {
      return ['Mongo URI', 'Database', 'Collection'];
    } else if (type === 'SQL Server') {
      return ['Host', 'Port', 'Username', 'Password', 'Database'];
    } else if (type === 'Cassandra' || type === 'CouchDB') {
      return ['Host', 'Port', 'Username', 'Password'];
    }
    return [];
  };

  const handleSave = () => {
    if (category && type) {
      onSave({ category, type, credentials });
      // Auto-close modal to redirect user back to NLP query page
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Configure Database</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Database Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as 'Structured' | 'Unstructured')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            >
              <option value="">Select category</option>
              <option value="Structured">Structured</option>
              <option value="Unstructured">Unstructured</option>
            </select>
          </div>

          {category && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Database Type
              </label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              >
                <option value="">Select type</option>
                {(category === 'Structured' ? structuredTypes : unstructuredTypes).map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          )}

          {type && (type === 'PostgreSQL' || type === 'MySQL' || type === 'SQL Server') && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-800">
                💡 Leave credentials empty to use demo mode with mock data
              </p>
            </div>
          )}

          {type && getCredentialFields().map((field) => (
            <div key={field}>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {field} {type === 'SQLite' && <span className="text-red-500">*</span>}
              </label>
              <input
                type={field.toLowerCase().includes('password') ? 'password' : 'text'}
                value={credentials[field] || ''}
                onChange={(e) =>
                  setCredentials({ ...credentials, [field]: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder={`Enter ${field.toLowerCase()}`}
              />
            </div>
          ))}
        </div>

        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!category || !type}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfigModal;
