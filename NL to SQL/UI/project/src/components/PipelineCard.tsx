import { LucideIcon } from 'lucide-react';

interface PipelineCardProps {
  title: string;
  icon: LucideIcon;
  content: string;
}

function PipelineCard({ title, icon: Icon, content }: PipelineCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <div className="flex items-center gap-2 mb-3">
        <Icon size={18} className="text-blue-600" />
        <h3 className="text-base font-semibold text-gray-900">{title}</h3>
      </div>
      <p className="text-sm text-gray-600 leading-relaxed">{content}</p>
    </div>
  );
}

export default PipelineCard;
