import { useState } from 'react';
import Header from './components/Header';
import ConfigModal, { DatabaseConfig } from './components/ConfigModal';
import QueryCard from './components/QueryCard';
import ExecutionResultCard from './components/ExecutionResultCard';
import VisualizationCard from './components/VisualizationCard';
import PipelineSection from './components/PipelineSection';

interface QueryResult {
  columns: string[];
  rows: Record<string, string | number | boolean | null>[];
  rewritten_query?: string;
  rewrite_explanation?: string;
  schema_context?: string;
  relevant_tables?: string[];
  sql_query?: string;
  validation_result?: Record<string, unknown>;
  validation_passed?: boolean;
  execution_result?: Record<string, unknown>;
  visualization?: Record<string, unknown>;
  explanation?: string;
}

function App() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [dbConfig, setDbConfig] = useState<DatabaseConfig | null>(null);
  const [result, setResult] = useState<QueryResult | null>(null);

  const mapDbTypeToApiValue = (type: string): string => {
    const mapping: Record<string, string> = {
      'PostgreSQL': 'postgresql',
      'MySQL': 'mysql',
      'SQLite': 'sqlite',
      'SQL Server': 'sqlserver',
    };
    return mapping[type] || 'sqlite';
  };

  const buildConnectionConfig = (config: DatabaseConfig | null): Record<string, string | number> => {
    if (!config || !config.credentials) return {};

    const { type, credentials } = config;

    // SQLite
    if (type === 'SQLite') {
      return credentials['File Path'] ? { db_path: credentials['File Path'] } : {};
    }

    // PostgreSQL, MySQL, SQL Server
    if (type === 'PostgreSQL' || type === 'MySQL' || type === 'SQL Server') {
      const connectionConfig: Record<string, string | number> = {};
      
      if (credentials['Host']) connectionConfig.host = credentials['Host'];
      if (credentials['Port']) connectionConfig.port = parseInt(credentials['Port']) || (type === 'PostgreSQL' ? 5432 : type === 'MySQL' ? 3306 : 1433);
      if (credentials['Database']) connectionConfig.database = credentials['Database'];
      if (credentials['Username']) connectionConfig.user = credentials['Username'];
      if (credentials['Password']) connectionConfig.password = credentials['Password'];

      return connectionConfig;
    }

    return {};
  };

  const handleRunQuery = async (query: string) => {
    try {
      setResult(null); // clear stale results before new request fires

      const dbType = dbConfig ? mapDbTypeToApiValue(dbConfig.type) : 'sqlite';
      const connectionConfig = buildConnectionConfig(dbConfig);
      const sessionId = crypto.randomUUID();

      const requestBody = {
        query,
        session_id: sessionId,
        db_type: dbType,
        connection_config: connectionConfig,
      };

      console.log("REQUEST:", requestBody); // Debug

      const res = await fetch('http://127.0.0.1:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!res.ok) {
        const errorData = await res.json();
        console.error("API ERROR:", errorData);
        alert(`API Error: ${errorData.detail || 'Unknown error'}`);
        return;
      }

      const data = await res.json();
      console.log("API RESULT:", data); // Debug
      setResult(data);
    } catch (err) {
      console.error("Error fetching query result:", err);
      alert(`Network Error: ${err instanceof Error ? err.message : 'Failed to connect to backend'}`);
    }
  };

  const handleClearResults = () => {
    setResult(null);
  };

  const handleSaveConfig = (config: DatabaseConfig) => {
    setDbConfig(config);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onConfigureClick={() => setIsModalOpen(true)} />

      <ConfigModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveConfig}
      />

      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* 🔥 Always show Query Section */}
        <div className="space-y-6">
          
          <QueryCard 
            onRunQuery={handleRunQuery} 
            onClear={handleClearResults}
            isConfigured={dbConfig !== null}
          />

          {/* 🔥 Show Results after Query */}
          {result && (
            <>
              <ExecutionResultCard
                columns={result.columns}
                rows={result.rows}
                executionResult={result.execution_result}
              />

              {result.visualization && (
                <VisualizationCard visualAssets={result.visualization} />
              )}

              <PipelineSection 
                rewrittenQuery={result.rewritten_query}
                rewriteExplanation={result.rewrite_explanation}
                schemaContext={result.schema_context}
                relevantTables={result.relevant_tables}
                sqlQuery={result.sql_query}
                validationResult={result.validation_result}
                validationPassed={result.validation_passed}
                executionResult={result.execution_result}
                explanation={result.explanation}
              />
            </>
          )}

        </div>
      </main>
    </div>
  );
}

export default App;
