export enum DifficultyLevel {
  BEGINNER = "beginner",
  INTERMEDIATE = "intermediate",
  ADVANCED = "advanced"
}

export enum ValidationStatus {
  PASSED = "passed",
  WARNING = "warning",
  FAILED = "failed",
  NOT_VALIDATED = "not_validated"
}

export interface Dependency {
  name: string;
  version?: string;
  isPinned: boolean;
}

export interface Notebook {
  id: string;
  path: string;
  title: string;
  description: string;
  author?: string;
  createdDate?: string;
  modifiedDate?: string;
  tags: string[];
  vertexAiServices: string[];
  pythonVersion?: string;
  dependencies: Dependency[];
  estimatedRuntime?: string;
  difficultyLevel?: DifficultyLevel;
  colabLink?: string;
  workbenchLink?: string;
  githubLink: string;
  validationStatus?: ValidationStatus;
  viewCount?: number;
}

export interface SearchFilters {
  tags?: string[];
  services?: string[];
  difficulty?: DifficultyLevel[];
  validationStatus?: ValidationStatus[];
}

export interface SearchResult {
  notebooks: Notebook[];
  totalCount: number;
  facets: {
    tags: Record<string, number>;
    services: Record<string, number>;
    difficulty: Record<string, number>;
  };
}
