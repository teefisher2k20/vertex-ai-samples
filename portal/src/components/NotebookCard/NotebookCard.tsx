import React from 'react';
import { Notebook, DifficultyLevel, ValidationStatus } from '@/types/notebook';
import { ExternalLink, Clock, Tag, AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react';

interface NotebookCardProps {
  notebook: Notebook;
  onClick?: (notebook: Notebook) => void;
}

export const NotebookCard: React.FC<NotebookCardProps> = ({ notebook, onClick }) => {
  const getDifficultyColor = (level?: DifficultyLevel) => {
    switch (level) {
      case DifficultyLevel.BEGINNER: return 'bg-green-100 text-green-800';
      case DifficultyLevel.INTERMEDIATE: return 'bg-blue-100 text-blue-800';
      case DifficultyLevel.ADVANCED: return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getValidationIcon = (status?: ValidationStatus) => {
    switch (status) {
      case ValidationStatus.PASSED:
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case ValidationStatus.WARNING:
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case ValidationStatus.FAILED:
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div 
      className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow cursor-pointer p-5"
      onClick={() => onClick?.(notebook)}
    >
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold text-gray-900 line-clamp-2 flex-1 mr-2">
          {notebook.title}
        </h3>
        {getValidationIcon(notebook.validationStatus)}
      </div>

      <p className="text-gray-600 text-sm mb-4 line-clamp-2 h-10">
        {notebook.description}
      </p>

      <div className="flex flex-wrap gap-2 mb-4">
        {notebook.vertexAiServices.slice(0, 3).map(service => (
          <span key={service} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full font-medium">
            {service}
          </span>
        ))}
        {notebook.tags.slice(0, 2).map(tag => (
          <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full flex items-center">
            <Tag className="w-3 h-3 mr-1" />
            {tag}
          </span>
        ))}
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500 pt-4 border-t border-gray-100">
        <div className="flex items-center gap-3">
          {notebook.difficultyLevel && (
            <span className={`px-2 py-0.5 rounded ${getDifficultyColor(notebook.difficultyLevel)}`}>
              {notebook.difficultyLevel}
            </span>
          )}
          {notebook.estimatedRuntime && (
            <span className="flex items-center">
              <Clock className="w-3 h-3 mr-1" />
              {notebook.estimatedRuntime}
            </span>
          )}
        </div>
        
        <div className="flex gap-2">
          {notebook.colabLink && (
            <a 
              href={notebook.colabLink}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center text-blue-600 hover:text-blue-800"
              onClick={(e) => e.stopPropagation()}
            >
              <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open in Colab" className="h-5" />
            </a>
          )}
          <a 
            href={notebook.githubLink}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1 hover:bg-gray-100 rounded"
            onClick={(e) => e.stopPropagation()}
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  );
};
