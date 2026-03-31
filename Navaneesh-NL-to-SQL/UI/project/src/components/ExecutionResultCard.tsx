interface Props {
  columns: string[];
  rows: Record<string, string | number | boolean | null>[];
  executionResult?: {
    success?: boolean;
    row_count?: number;
    execution_time?: number;
    error?: string | null;
  };
}

function ExecutionResultCard({ columns, rows, executionResult }: Props) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Query Results
      </h2>

      {/* Execution Info */}
      {executionResult && (
        <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="flex items-center gap-4 text-sm">
            <span className={executionResult.success ? 'text-green-600' : 'text-red-600'}>
              {executionResult.success ? '✅ Success' : '❌ Failed'}
            </span>
            {typeof executionResult.row_count === 'number' && (
              <span className="text-gray-600">
                Rows: {executionResult.row_count}
              </span>
            )}
            {typeof executionResult.execution_time === 'number' && (
              <span className="text-gray-600">
                Time: {executionResult.execution_time.toFixed(3)}s
              </span>
            )}
          </div>
          {executionResult.error && (
            <p className="text-sm text-red-600 mt-2">Error: {executionResult.error}</p>
          )}
        </div>
      )}

      {/* ONLY TABLE - NO EXPLANATION */}
      {rows.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full border border-gray-200">
            <thead>
              <tr className="border-b bg-gray-50">
                {columns.map((col) => (
                  <th
                    key={col}
                    className="px-4 py-3 text-left text-sm font-medium text-gray-700"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {rows.map((row, idx) => (
                <tr key={`${idx}-${columns.map(c => row[c]).join('|')}`} className="border-b hover:bg-gray-50">
                  {columns.map((col) => (
                    <td
                      key={col}
                      className="px-4 py-3 text-sm text-gray-900"
                    >
                      {String(row[col] ?? '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          
          <p className="text-sm text-gray-500 mt-2">
            Showing {rows.length} row{rows.length !== 1 ? 's' : ''}
          </p>
        </div>
      )}

      {rows.length === 0 && (
        <p className="text-gray-500 text-center py-8">No results found</p>
      )}
    </div>
  );
}

export default ExecutionResultCard;