interface Props {
  rewrittenQuery?: string;
  rewriteExplanation?: string;
  schemaContext?: string;
  relevantTables?: string[];
  sqlQuery?: string;
  validationResult?: Record<string, unknown>;
  validationPassed?: boolean;
  executionResult?: Record<string, unknown>;
  explanation?: string;
}

function PipelineSection({ 
  rewrittenQuery, 
  rewriteExplanation,
  schemaContext, 
  relevantTables,
  sqlQuery, 
  validationResult,
  validationPassed,
  executionResult,
  explanation 
}: Props) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Pipeline</h2>
      <div className="space-y-6">
      
      {/* Query Rewriter */}
      {(rewrittenQuery || rewriteExplanation) && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <span>📝</span> Query Rewriter
          </h2>
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            {rewrittenQuery && (
              <p className="text-sm text-gray-700 mb-2">
                <span className="font-medium">Rewritten: </span>{rewrittenQuery}
              </p>
            )}
            {rewriteExplanation && (
              <p className="text-sm text-gray-600">
                <span className="font-medium">Explanation: </span>{rewriteExplanation}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Schema */}
      {(schemaContext || (relevantTables && relevantTables.length > 0)) && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <span>📚</span> Schema
          </h2>
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            {relevantTables && relevantTables.length > 0 && (
              <p className="text-sm text-gray-700 mb-2">
                <span className="font-medium">Relevant tables: </span>
                {relevantTables.join(", ")}
              </p>
            )}
            {schemaContext && (
              <p className="text-sm text-gray-600 whitespace-pre-wrap">{schemaContext}</p>
            )}
          </div>
        </div>
      )}

      {/* Query Generation */}
      {sqlQuery && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <span>🧮</span> Generated SQL
          </h2>
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <pre className="text-sm text-blue-900 font-mono whitespace-pre-wrap overflow-x-auto">
              {sqlQuery}
            </pre>
          </div>
        </div>
      )}

      {/* Validation */}
      {validationResult && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <span>{validationPassed ? '✅' : '❌'}</span> Validation
          </h2>
          <div className={`rounded-lg p-4 border ${validationPassed ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
            <p className={`text-sm ${validationPassed ? 'text-green-800' : 'text-red-800'}`}>
              {validationPassed ? '✅ SQL validation passed.' : '❌ SQL validation failed.'}
            </p>
            {validationResult.explanation !== undefined && validationResult.explanation !== null && (
              <p className="text-sm text-gray-700 mt-2">{String(validationResult.explanation)}</p>
            )}
          </div>
        </div>
      )}

      {/* Query Execution */}
      {executionResult && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <span>⚙️</span> Query Execution
          </h2>
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <p className="text-sm text-gray-700">
              {executionResult.success ? '✅' : '❌'} Executed query. 
              {typeof executionResult.row_count === 'number' && ` Rows returned: ${executionResult.row_count}`}
            </p>
            {typeof executionResult.execution_time === 'number' && (
              <p className="text-sm text-gray-600 mt-1">
                Execution time: {executionResult.execution_time}ms
              </p>
            )}
          </div>
        </div>
      )}

      {/* NLP Explanation */}
      {explanation && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <span>💡</span> NLP Explanation
          </h2>
          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
            <p className="text-sm text-gray-700 leading-relaxed">{explanation}</p>
          </div>
        </div>
      )}

    </div>
    </div>
  );
}

export default PipelineSection;
