import { BarChart3 } from 'lucide-react';

interface Props {
  visualAssets: Record<string, unknown>;
}

function VisualizationCard({ visualAssets: _visualAssets }: Props) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Visualization</h2>
      <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 h-64 flex items-center justify-center">
        <div className="text-center">
          <BarChart3 size={48} className="mx-auto text-gray-400 mb-2" />
          <p className="text-sm font-medium text-gray-500">Chart</p>
        </div>
      </div>
    </div>
  );
}

export default VisualizationCard;
